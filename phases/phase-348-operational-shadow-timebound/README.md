# Phase 348: concurrent operational shadow time bound

Date: 2026-09-22

## Why this phase exists

The first Gate E probe exposed a real concurrency defect. A timed-out
ripgrep lookup fell through to a second Python tree walk, and the server's
worker lock serialized model-unloaded mechanical requests behind that work.
The initial run completed `38/40` requests, had two client timeouts, and
reported a p95 of `2051.751 ms`.

## Changes

1. A ripgrep deadline now returns a bounded `search_timeout` abstention rather
   than starting a second full-tree scan.
2. Broad literal search has a `0.75 s` hard accelerator budget.
3. Mechanical-only and native-upstream modes do not take the in-process model
   generation lock when no Transformers model is loaded. A loaded model still
   retains the lock around generation.
4. The shadow receipt now reports accepted-only and per-action latency so
   deliberate health failures do not masquerade as successful-task latency.

## Final receipt

The fresh concurrent run used four workers and ten rounds against the
materialized package at
`D:\models\_wrench-release-candidate-search-concurrent`:

- `40/40` requests completed, with zero errors.
- Accepted-only p50/p95 was `3.153/17.770 ms`.
- `33` requests used the mechanical fast path and model calls were `0`.
- Cancellation recovery was accepted in `1.713 ms`.
- RAM reserve passed before and after at `53.82%` and `53.54%` available.
- VRAM was not present in this mechanical-only process, so its reserve check
  was vacuously safe.

The intentionally unreachable health probe remained around two seconds and
is reported separately under `latency_by_action_ms`; it is not included in
the accepted-only success distribution.

Receipts: `receipt.json` records the original failure,
`receipt-r2.json` records the first bounded-search repair,
`receipt-r3.json` records the accepted-only breakdown before lock repair,
and `receipt-r4.json` is the final passing concurrent run.

## Verification boundary

This closes a local Gate E mechanical-only concurrency and recovery slice. It
does not establish native dense 4M attention quality, learned MiniMax parity,
independent RTX 5060 Ti execution, or production approval.
