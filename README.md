# Manage Codex Thread Status

Keep Codex thread titles honest and visible:

```text
⏳ Implement thread status management
🚨 Approve production credentials
✅ Implement thread status management
```

This open-source Codex Skill synchronizes the status prefix with live work and renames the title body only when the task topic materially changes. It supports interactive threads, cross-workspace coordination, and automations that do not expose the native thread-title tool.

## What it does

| Prefix | Meaning |
| --- | --- |
| `⏳` | Work is active or completion is unclear |
| `🚨` | Progress requires an action only the user can take |
| `✅` | The current request is fully delivered |

- Preserves the title body when only status changes.
- Renames the body when the task itself materially changes.
- Prefers Codex's native title tool for immediate desktop updates.
- Includes a small Python fallback for tool-less automations with `CODEX_THREAD_ID`.
- Uses no daemon, polling loop, database, or third-party Python dependency.

## Install

```bash
git clone https://github.com/clarkchenkai/manage-codex-thread-status.git \
  "$HOME/.codex/community/manage-codex-thread-status"
mkdir -p "$HOME/.codex/skills"
ln -s "$HOME/.codex/community/manage-codex-thread-status/skills/manage-codex-thread-status" \
  "$HOME/.codex/skills/manage-codex-thread-status"
```

Then invoke it in Codex:

```text
Use $manage-codex-thread-status to keep this thread title synchronized with its live status and current topic.
```

## Global behavior

To make the behavior a default across workspaces, add a compact rule to `~/.codex/AGENTS.md`:

```markdown
When the thread-title tool is available, update the current title at the start and end of every user turn. Use exactly one prefix: `⏳` while work is active, `🚨` only when blocked on the user, and `✅` only when fully complete. Preserve the title body unless the task topic materially changes. If the native tool is unavailable but `CODEX_THREAD_ID` exists, use the `manage-codex-thread-status` fallback script. Do not let a status-update failure block the underlying task.
```

Existing threads may not reload later changes to global instructions. Validate global changes in a new thread.

## Automation fallback

```bash
python3 "$HOME/.codex/skills/manage-codex-thread-status/scripts/set_thread_status.py" in-progress
python3 "$HOME/.codex/skills/manage-codex-thread-status/scripts/set_thread_status.py" status
python3 "$HOME/.codex/skills/manage-codex-thread-status/scripts/set_thread_status.py" done
```

Use `needs-attention` for `🚨`. Add `--title-body "New topic"` when the task topic changes. If an automation has an atomic first step—such as capturing time, obtaining a lease, or running a probe—complete that step first, then set `⏳` immediately afterward.

## Requirements

- Codex with `thread/read` and `thread/name/set` app-server methods.
- `CODEX_THREAD_ID` for the fallback path.
- Python 3; standard library only.

The app-server surface used by the fallback may evolve. Prefer the native Codex title tool whenever it is available.

## Validation

- Skill structure validation.
- Python syntax and privacy scans.
- Live cross-workspace runtime test: `✅ → ⏳ → status readback → ✅`.

Desktop UI refresh should still be confirmed on the Codex version where the Skill is installed.

## License

MIT
