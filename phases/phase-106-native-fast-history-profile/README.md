# Phase 106: native fast-history profile

The portable FreeToken launcher now exposes an explicit `-FastHistory` profile.
It keeps the complete raw request and native prompt accounting, while the
serving overlay skips attention and MLP work before the recent-token boundary.
The default launcher remains unchanged and does not enable this policy.

## Existing native evidence

- 2M direct input with history-layer skip: `2,004,136` prompt tokens,
  `truncated=false`, HTTP 200, `84,851.710 ms`
- 4M direct input with history-layer skip: `3,999,942` prompt tokens,
  `truncated=false`, HTTP 200, `129,290.508 ms`
- 2M direct input without this policy: `1,999,929` prompt tokens,
  `truncated=false`, HTTP 200, `1,287,078.199 ms`
- Generated launcher PowerShell AST parse: `0` errors
- Full repository tests after the launcher change: `120 passed, 8 warnings`

The history-layer skip measurements are capacity and throughput evidence only.
They do not establish retrieval quality, MiniMax parity, safety parity, or a
production default. The profile is therefore opt-in.

The public package revision containing the profile is
`86d72453123fbdd97bb3666f390f10d787922321`. The boundary is request-relative:
the launcher sets `WRENCH_HISTORY_SKIP_LAYERS_BEFORE=auto` and the overlay
computes `actual_input_len - keep_tokens` per request, so 2M and 4M inputs use
the same endpoint safely.
