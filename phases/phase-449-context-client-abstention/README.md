# Phase 449: context-client missing-user abstention

Date: 2026-09-23

## Change

Static control-flow review found that `_bounded_messages_from_context` could
index `user_messages[-1]` when a request had a nonempty `context_query` but no
user-role message. That raised `IndexError` instead of returning the client's
structured abstention result. The client now abstains with
`qwen_context_user_message_missing` when no current user message exists or its
content is whitespace-only.

## Evidence and limits

- The changed function was read after editing, and `git diff --check` passed
  for the changed Python and phase documentation files.
- No tests were added or run in this phase. Runtime behavior is therefore not
  independently verified, and this receipt does not close Gate A or Gate E.
- No server lifecycle, verifier policy, model, provider, or credential behavior
  changed.
