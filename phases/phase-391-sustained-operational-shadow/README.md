# Phase 391: sustained operational shadow

The current portable package completed a larger mechanical-only Gate E shadow
with `8` concurrent workers and `25` rounds, for `200/200` completed requests.
There were zero errors, zero model calls, and all bounded-response, cancellation,
and resource-reserve checks passed.

- Accepted requests: `68`
- Explicit abstentions: `132`
- Accepted-only p50/p95 latency: `3.517/26.465 ms`
- All-request p50/p95 latency: `3.968/2053.154 ms`
- Cancellation recovery: `2.019 ms`, accepted
- RAM available ratio: `55.62%` before and `55.16%` after
- VRAM reserve: passed with no CUDA device present

The approximately two-second all-request tail is the intentionally unreachable
health-read abstention and remains separated from the successful-task
distribution. Local runtime cost is still unpriced, and this phase does not
close the stronger-model canary, paid accounting, model parity, or production
approval gates.

Evidence: `receipt.json`.

The initial Phase 391 receipt exposed a provenance gap: its digest covered
in-memory request rows that were not persisted. The operational result remains
valid as a bounded run, but the hash is not independently recomputable from
that artifact. Phase 392 reran the same workload with persisted rows and a
verifiable digest.
