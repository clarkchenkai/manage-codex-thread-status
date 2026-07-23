#!/usr/bin/env python3
"""Set or read the current Codex thread title status through app-server."""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import shutil
import subprocess
import sys
import time


STATUS = {"in-progress": "⏳", "needs-attention": "🚨", "done": "✅"}
ACTIONS = (*STATUS, "status")
PREFIX = re.compile(r"^[✅🚨⏳]\s+")


def send(process: subprocess.Popen, message: dict) -> None:
    process.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
    process.stdin.flush()


def receive(process: subprocess.Popen, request_id: int, timeout: float = 2.0) -> dict | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([process.stdout], [], [], deadline - time.monotonic())
        if not ready:
            return None
        line = process.stdout.readline()
        if not line:
            return None
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("id") == request_id:
            return message
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("status", choices=ACTIONS)
    parser.add_argument("--thread-id", default=os.environ.get("CODEX_THREAD_ID"))
    parser.add_argument("--title-body", help="Replace the title body while setting a status")
    args = parser.parse_args()
    if args.status == "status" and args.title_body is not None:
        parser.error("--title-body cannot be used with status")

    codex = shutil.which("codex")
    if not args.thread_id or not codex:
        print(json.dumps({"ok": False, "error": "CODEX_THREAD_ID or codex is unavailable"}))
        return 2

    process = subprocess.Popen(
        [codex, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    try:
        send(process, {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "set-thread-status", "version": "1.0.0"}, "capabilities": {"experimentalApi": True}}})
        if not receive(process, 1):
            print(json.dumps({"ok": False, "error": "app-server initialize failed"}))
            return 2
        send(process, {"method": "initialized", "params": {}})
        send(process, {"id": 2, "method": "thread/read", "params": {"threadId": args.thread_id, "includeTurns": False}})
        response = receive(process, 2)
        thread = ((response or {}).get("result") or {}).get("thread") or {}
        current = thread.get("name")
        if not current:
            print(json.dumps({"ok": False, "error": "thread has no title"}))
            return 2
        if args.status == "status":
            print(json.dumps({"ok": True, "thread_id": args.thread_id, "title": current}, ensure_ascii=False))
            return 0

        body = args.title_body.strip() if args.title_body is not None else PREFIX.sub("", current).strip()
        if not body:
            print(json.dumps({"ok": False, "error": "title body is empty"}))
            return 2
        updated = f"{STATUS[args.status]} {body}"
        if updated != current:
            send(process, {"id": 3, "method": "thread/name/set", "params": {"threadId": args.thread_id, "name": updated}})
            if not receive(process, 3):
                print(json.dumps({"ok": False, "error": "thread/name/set failed"}))
                return 2
        print(json.dumps({"ok": True, "thread_id": args.thread_id, "title": updated}, ensure_ascii=False))
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    sys.exit(main())
