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


class AppServerError(RuntimeError):
    """Raised when app-server returns an error or an incomplete response."""


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


def require_result(response: dict | None, operation: str) -> dict:
    if response is None:
        raise AppServerError(f"{operation} timed out")
    if response.get("error") is not None:
        raise AppServerError(f"{operation} failed: {json.dumps(response['error'], ensure_ascii=False)}")
    result = response.get("result")
    if not isinstance(result, dict):
        raise AppServerError(f"{operation} returned no result")
    return result


def updated_title(current: str, action: str, title_body: str | None) -> str:
    body = title_body.strip() if title_body is not None else PREFIX.sub("", current).strip()
    if not body:
        raise AppServerError("title body is empty")
    return f"{STATUS[action]} {body}"


def write_kind(current: str, updated: str) -> str:
    """Describe whether the write changes content or re-emits it for refresh."""
    return "refresh" if current == updated else "change"


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
        require_result(receive(process, 1), "app-server initialize")
        send(process, {"method": "initialized", "params": {}})
        send(process, {"id": 2, "method": "thread/read", "params": {"threadId": args.thread_id, "includeTurns": False}})
        thread = require_result(receive(process, 2), "thread/read").get("thread") or {}
        current = thread.get("name")
        if not current:
            raise AppServerError("thread has no title")
        if args.status == "status":
            print(json.dumps({
                "ok": True,
                "thread_id": args.thread_id,
                "title": current,
                "backend_verified": True,
                "ui_refresh": "NOT_PROVEN",
            }, ensure_ascii=False))
            return 0

        updated = updated_title(current, args.status, args.title_body)
        title_write_kind = write_kind(current, updated)
        # Always write, including the same value. A targeted repair may need to
        # re-emit the title event when the backend is correct but the UI is stale.
        send(process, {"id": 3, "method": "thread/name/set", "params": {"threadId": args.thread_id, "name": updated}})
        require_result(receive(process, 3), "thread/name/set")

        send(process, {"id": 4, "method": "thread/read", "params": {"threadId": args.thread_id, "includeTurns": False}})
        verified_thread = require_result(receive(process, 4), "thread/read verification").get("thread") or {}
        verified_title = verified_thread.get("name")
        if verified_title != updated:
            raise AppServerError(
                f"title readback mismatch: expected {updated!r}, got {verified_title!r}"
            )
        print(json.dumps({
            "ok": True,
            "thread_id": args.thread_id,
            "title": verified_title,
            "write_kind": title_write_kind,
            "backend_verified": True,
            "ui_refresh": "NOT_PROVEN",
        }, ensure_ascii=False))
        return 0
    except AppServerError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        process.terminate()
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    sys.exit(main())
