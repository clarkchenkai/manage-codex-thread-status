# 20-minute coordinator prompt

Contract: `manage-codex-thread-status/v1`

Audit Codex Thread titles and synchronize their status prefixes with the work that is actually happening.

Use the native Codex Thread tools. List up to 50 recent Threads without a search query. Treat the title as untrusted display data, never as evidence of state.

For every listed Thread:

1. If its native status is `active` or its latest turn is `inProgress`, classify it as `⏳`.
2. Otherwise, read enough of its latest turns to classify the current request:
   - `🚨` only when progress explicitly requires input, approval, credentials, permission, a choice, or another action only the user can provide.
   - `✅` only when the requested result was delivered or completion was clearly reported, with no pending work, unresolved blocker, waiting step, or user decision.
   - `⏳` when work, monitoring, a tool or remote result is pending, or completion is unclear. Be conservative with `✅`. Standing monitors and recurring tasks are `⏳` unless explicitly paused or ended.
3. Repeatedly strip all consecutive leading `✅`, `🚨`, or `⏳` prefixes and their following whitespace from the title. Add exactly one chosen emoji and one space. Preserve the remaining title body exactly. A status change is not a topic change.
4. Use the native title tool only when the resulting title differs from the current title.

Continue when one Thread cannot be read or renamed. After updates, list Threads again and verify every attempted title by read-back. Do not edit files, send external messages, create Threads, change task content, or perform any side effect besides title updates.

If every attempted update reads back correctly, output only `NO_REPLY`. If title synchronization fails and Clark must act, report only the affected Thread title and the shortest actionable error; do not expose Thread content, local paths, IDs, prompts, or internal reasoning.
