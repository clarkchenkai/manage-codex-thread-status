# Manage Codex Thread Status

Keep the Codex sidebar useful by synchronizing every recent Thread title with live work:

```text
⏳ Implement thread status management
🚨 Approve production credentials
✅ Implement thread status management
```

The product has two layers:

1. A Codex heartbeat Automation audits recent Threads every 20 minutes and repairs stale prefixes.
2. The Skill gives interactive Agents an immediate per-turn update contract and a tool-less single-Thread fallback.

The scheduled cross-Thread audit is required. Per-turn Agent behavior or the fallback script alone does not satisfy the product goal.

## Status contract

| Prefix | Meaning |
| --- | --- |
| `⏳` | Work, monitoring, tools, or remote results are pending; or completion is unclear |
| `🚨` | Progress requires an action only the user can take |
| `✅` | The current request is fully delivered with nothing pending |

Use exactly one prefix. Be conservative with `✅`. Preserve the title body when only status changes.

## Install the Skill

```bash
git clone https://github.com/clarkchenkai/manage-codex-thread-status.git \
  "$HOME/.codex/community/manage-codex-thread-status"
mkdir -p "$HOME/.codex/skills"
ln -s "$HOME/.codex/community/manage-codex-thread-status/skills/manage-codex-thread-status" \
  "$HOME/.codex/skills/manage-codex-thread-status"
```

Then use `$manage-codex-thread-status` to create one active 20-minute heartbeat Automation from the canonical prompt in `references/automation-prompt.md`. Read the saved Automation back before calling installation complete.

Validate the installed product, not only the Skill files:

```bash
python3 "$HOME/.codex/skills/manage-codex-thread-status/scripts/set_thread_status.py" installation-status
```

Success requires `ok: true`, one active 20-minute heartbeat, the exact canonical prompt, and the global Skill link.

## Runtime behavior

Each scheduled run:

- lists up to 50 recent Threads;
- trusts native active/in-progress state over the existing title;
- reads recent turns when terminal state is semantically ambiguous;
- applies `⏳`, `🚨`, or `✅` conservatively;
- preserves title bodies during status-only changes;
- uses native title updates and verifies read-back;
- stays silent with `NO_REPLY` when synchronization succeeds.

The coordinator itself is a standing monitor and normally remains `⏳` while active.

## Single-Thread fallback

For an environment without the native title tool but with `CODEX_THREAD_ID`:

```bash
python3 "$HOME/.codex/skills/manage-codex-thread-status/scripts/set_thread_status.py" in-progress
python3 "$HOME/.codex/skills/manage-codex-thread-status/scripts/set_thread_status.py" needs-attention
python3 "$HOME/.codex/skills/manage-codex-thread-status/scripts/set_thread_status.py" done
```

The fallback writes and reads one known Thread through `codex app-server`. It is not the scheduled coordinator and cannot classify other Threads.

## Validation

- Skill metadata and Python syntax pass.
- Unit and Automation contract tests pass.
- The global Skill link and active 20-minute Automation read back correctly.
- A real audit proves active → `⏳`, user-blocked → `🚨`, and delivered → `✅`.
- The sidebar visibly refreshes after native title updates.

## License

MIT
