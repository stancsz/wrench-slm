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
- Full repository tests after the launcher change: `122 passed, 10 warnings`

The history-layer skip measurements are capacity and throughput evidence only.
They do not establish retrieval quality, MiniMax parity, safety parity, or a
production default. The profile is therefore opt-in.

The public package revision containing the profile, lookup fix, and PowerShell
launcher fix is `5176fd64ff511a8f959cd505966d8af02b8efc9e`. The boundary is
request-relative. The latest public revision is
`85389af2c506d5fe21b842edf189c2212349b351` and also rejects empty unified
diffs at the verifier boundary:
the launcher sets `WRENCH_HISTORY_SKIP_LAYERS_BEFORE=auto` and the overlay
computes `actual_input_len - keep_tokens` per request, so 2M and 4M inputs use
the same endpoint safely.

## Retrieval-quality canary

The first real 2M fast-history lookup canary did not pass. It processed
`861,242` prompt tokens in `118.517 ms`, but returned the invalid path
`wrench.proposal.v1` instead of the expected
`src/wrench_harness/worker.py`. The receipt is
`fast-history-2m-lookup.json`. This keeps the release boundary honest: native
capacity and fast-path throughput are demonstrated, while retrieval quality
and MiniMax parity remain open.

The failure was traced to a deterministic routing bug: the protocol token
`wrench.proposal.v1` was being treated as a candidate filename before the
historical lookup route ran. The route now excludes reserved Wrench schema
tokens. After the fix, the same 2M canary passed at `112.471 ms`, and a
`4,004,004` prompt-token canary passed at `460.155 ms`; both returned
`src/wrench_harness/worker.py` with `model_calls=0`. These are deterministic
embedded lookup proofs, not a claim of general LLM retrieval quality or
MiniMax parity.

The portable launcher now defaults to `ft.exe`, avoiding the Windows
PowerShell `ft` alias for `Format-Table`. An explicit FreeToken executable
path can still be supplied when the binary is not on `PATH`.

A short 48-token semantic probe completed in 1.874 seconds, but produced
an empty diff. The new verifier rejects that output as
`invalid_patch_diff`; fast semantic mode must therefore be treated as a fast
fail until patch content is supplied or the model is fine-tuned to generate a
real diff.

The full portable 220-case replay preserved `200/200` outcome matches and
`0` prohibited accepts on the mechanical fast path. The remaining 20 eligible
patch-draft requests were sent to the real FreeToken model fallback; all 20
exceeded the 10-second client timeout under the current 8GB offload profile.
The measured replay median was `0.524 ms`, but p95 was `10,030.754 ms` because
of those semantic generations. This is now the main latency blocker for
practical fallback work.
