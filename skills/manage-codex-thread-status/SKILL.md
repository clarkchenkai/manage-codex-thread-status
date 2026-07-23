---
name: manage-codex-thread-status
description: Keep Codex thread titles synchronized with live work using `⏳`, `🚨`, and `✅`. Use when installing or running the 20-minute cross-thread status coordinator, auditing sidebar title drift, repairing stale prefixes, or updating one thread from an interactive task or tool-less automation.
---

# Codex Thread Status Manager

Keep every visible title aligned with the Thread's current work. Use the scheduled coordinator as the cross-thread safety net and per-turn updates for immediate feedback.

## Status contract

- `⏳`: Work is active, a monitor is running, a tool or remote result is pending, or completion is unclear.
- `🚨`: Progress explicitly requires input, approval, credentials, permission, a choice, or another action only the user can provide.
- `✅`: The current request is delivered, with no pending work, blocker, wait step, or user decision.

Use exactly one status emoji and one space. Be conservative with `✅`. Do not use `🚨` merely because an error occurred while the Agent can still handle it.

Strip all consecutive existing status prefixes before writing the new one. Preserve the title body when only status changes. Rename the body only when the task topic materially changes.

## Install the 20-minute coordinator

This is the primary product workflow. Create one Codex heartbeat automation that runs every 20 minutes in a stable coordinator Thread. Use the complete prompt in [references/automation-prompt.md](references/automation-prompt.md); do not summarize or partially copy it.

After creation, read the Automation back and verify:

1. It is active and scheduled every 20 minutes.
2. Its prompt lists Threads, reads ambiguous terminal state, applies all three status classes, preserves title bodies, and performs read-back.
3. It uses native `set_thread_title` updates so the desktop receives the title event.
4. A real run corrects at least one stale active title and correctly preserves one waiting-user and one completed title.

Run the deterministic deployment read-back after creating or updating the Automation:

```bash
python3 <skill-directory>/scripts/set_thread_status.py installation-status
```

It must report `ok: true`, exactly one active 20-minute Automation, a verified global Skill link, and an exact canonical-prompt match.

The coordinator is a standing monitor, so its own title normally remains `⏳` while the Automation is active.

## Per-turn workflow

Use this as the fast path between scheduled audits:

1. At the start of a user turn, set the current Thread to `⏳`.
2. Keep `⏳` while work, monitoring, tools, or remote results remain pending.
3. Before yielding for an action only the user can take, set `🚨`.
4. Before a final response, set `✅` only when the current request is fully delivered.

The scheduled coordinator repairs missed or stale per-turn writes. Per-turn compliance alone is not the product.

## Native and fallback paths

Prefer the native Codex thread-title tool. It reaches the desktop event path and can update any Thread selected by the coordinator.

When the native tool is unavailable and `CODEX_THREAD_ID` exists, update only that known Thread with:

```bash
python3 <skill-directory>/scripts/set_thread_status.py in-progress
python3 <skill-directory>/scripts/set_thread_status.py needs-attention
python3 <skill-directory>/scripts/set_thread_status.py done
python3 <skill-directory>/scripts/set_thread_status.py status
```

Use `--thread-id <id>` for a known target and `--title-body "New topic"` only when the topic changed. The fallback re-sends same-title writes and reads the backend title back, but it cannot prove desktop rendering.

Do not use the fallback to discover or semantically classify other Threads. Cross-thread classification belongs to the scheduled native-tool coordinator.

## Boundaries

- Do not edit Codex session indexes or infer state from database files.
- Do not create a separate polling daemon; use the Codex heartbeat Automation.
- Do not expose thread contents, local paths, or internal reasoning in Automation output.
- Do not let one unreadable Thread abort the rest of an audit.
- Do not rewrite title bodies during a status-only audit.
- Do not report backend read-back as proof of desktop rendering.

## Verification

Prove each layer separately:

1. Skill: metadata validation, Python syntax, unit tests, and Automation contract tests pass.
2. Deployment: the global Skill link and 20-minute Automation both exist and read back correctly.
3. Runtime: an active Thread becomes `⏳`, a user-blocked Thread becomes or remains `🚨`, and a fully delivered Thread becomes or remains `✅`.
4. UI: the sidebar visibly shows the corrected prefixes after a native update.

Do not call the product complete if the scheduled Automation is absent or no real cross-thread run has passed.
