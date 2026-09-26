# Offline mixed-lifecycle ledger bridge

Status: implemented and verified with focused synthetic `unittest` cases on
2026-09-26. This is an offline receipt adapter, not a client hook or usage
collector.

`wrench_harness.mixed_lifecycle_ledger_bridge.bridge()` converts bounded
`wrench.mixed-lifecycle-ledger.v1` input into the paired reporter's existing
`wrench.paired-frontier-savings-input.v1` format. It represents local and
frontier attempts, retries, fallbacks, tools, verifier calls, exact or
estimated token usage, and unknown usage/cost. It preserves the narrow
frontier-only bridge contract.

The adapter rejects oversized and malformed documents before accepting them.
Missing, duplicate, unmatched, explicitly unknown, wrong-route, or
wrong-counter usage taints all token counts for that arm, so partial totals
cannot enter the reporter. Unknown cost remains separate from exact token
accounting. Caller-supplied outcomes marked `independently_verified` are
downgraded to `user_reported`; the returned audit labels all evidence
`caller_supplied_untrusted`. Therefore caller-authored claims cannot qualify
for the reporter's successful-task mean.

Focused offline tests pass 7/7. A regression rejects `not_run` work calls with
local/frontier routes before usage reconciliation; `none/not_run` remains a
non-call with not-applicable usage. This fixes the reviewed false-call-count
path.

In the synthetic fixture, the general
all-usage arithmetic reports 31 baseline versus 22 Wrench frontier tokens, or
29.032258% reduction. Both outcome declarations are untrusted and downgraded,
so the success-qualified pair count is zero and its average is unavailable.
These values test schema conversion and arithmetic only. They are not observed
Wrench savings, a model result, or evidence of real task success.

No client, provider, endpoint, local model, real task corpus, or external
telemetry was used. The adapter does not authenticate dispatch, usage,
serializer/tokenizer parity, consent, or outcome truth. Actual successful-task
frontier savings remain N/A with zero eligible matched pairs.
