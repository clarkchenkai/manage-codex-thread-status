---
name: manage-codex-thread-status
description: Keep Codex thread titles synchronized with live work using `⏳`, `🚨`, and `✅`, and rename the title body when the task topic materially changes. Use when enabling, auditing, or repairing thread status across workspaces, interactive tasks, and automations, including environments that lack the native thread-title tool but expose `CODEX_THREAD_ID`.
---

# Codex Thread Status Manager

Keep the user-visible thread title aligned with both the current state and the current topic. Prefer the native Codex thread-title tool. Use the bundled fallback only when that tool is unavailable.

## Status contract

- `⏳`: Work is active, monitoring is running, a tool or remote result is pending, or completion is unclear.
- `🚨`: Progress is blocked on input, approval, credentials, permission, or a decision only the user can provide.
- `✅`: The current request is delivered with no pending work, unresolved blocker, wait step, or user decision.

Use exactly one status emoji and one space. Preserve the title body when only the status changes. Rename the body only when the task topic materially changes; do not rename it for routine implementation steps.

## Per-turn workflow

1. At the start of a user turn, set the current thread to `⏳` before beginning ordinary investigation or implementation.
2. Keep `⏳` while work remains active.
3. Before asking for an action that only the user can take, set `🚨`.
4. Before the final response, set `✅` only if the current request is fully complete.
5. If the topic changed, update the title body at the same time as the next status change.

This workflow is Agent-driven. A Skill is not a lifecycle hook and does not receive app spinner events. A thread created before these instructions were installed may continue working with a stale prefix because its existing context does not dynamically reload the new rule.

## Execution paths

### Native tool

Use the Codex thread-title tool whenever it is available. It is the preferred path because the desktop UI receives the update directly.

### Fallback for tool-less tasks

If the native tool is unavailable and `CODEX_THREAD_ID` is present, resolve this Skill's directory and run:

```bash
python3 <skill-directory>/scripts/set_thread_status.py in-progress
python3 <skill-directory>/scripts/set_thread_status.py status
python3 <skill-directory>/scripts/set_thread_status.py done
```

Use `needs-attention` for `🚨`. To update the topic body as well:

```bash
python3 <skill-directory>/scripts/set_thread_status.py in-progress --title-body "Implement status-aware thread titles"
```

The fallback uses Python's standard library and a short-lived `codex app-server` process. A status failure must not block the underlying task.

Status-setting calls deliberately re-send `thread/name/set` even when the backend title already equals the requested value. This gives a targeted repair one chance to re-emit the title event when the desktop UI is stale. Backend readback still does not prove UI refresh.

For a specific older thread that is visibly active but has a stale prefix, a current coordinator may repair only that thread:

```bash
python3 <skill-directory>/scripts/set_thread_status.py in-progress --thread-id <thread-id>
```

Resolve the target from the native task list or the visible UI. The fallback's short-lived app-server cannot prove the desktop process's live spinner state, so it must not scan or infer which threads are active.

## Automation ordering

If an automation requires an atomic first step such as capturing time, obtaining a lease, or running a probe, complete that step first and then immediately set `⏳`. Set `✅` before a successful `NO_REPLY` or final response. Set `🚨` only when the automation genuinely needs user action.

Add the fallback calls explicitly to automation prompts that do not expose the native title tool. Do not assume a global instruction will override a more specific automation contract.

## Boundaries

- Do not poll, create a daemon, or scan historical threads.
- Do not edit Codex session indexes directly.
- Do not treat an error as `🚨` while the agent can still handle it.
- Existing threads may not reload later changes to global instructions or automation prompts. They require a targeted coordinator repair or a newly created thread; receiving another user message does not prove that the old context reloaded the rule.
- A Skill stored in one workspace does not automatically govern every other workspace. Install it globally or reference its absolute directory from the automation that uses it.

## Verification

Prove each relevant layer separately:

1. Configuration: the Skill or automation prompt references the correct execution path.
2. Static validation: Skill metadata and Python syntax pass.
3. Runtime: an active test thread changes from `✅` to `⏳`, the write receives no RPC error, a second `thread/read` reads back `⏳`, and completion changes it to `✅`.
4. UI: confirm the Codex sidebar visibly refreshes; a backend readback alone is not UI proof.

Report untested layers as `NOT RUN` and unobserved UI behavior as `NOT PROVEN`.
