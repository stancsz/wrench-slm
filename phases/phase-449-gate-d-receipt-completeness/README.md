# Phase 449: Gate D receipt completeness hardening

Date: 2026-09-23

## Changes

- The client now retains a prompt-free receipt for every endpoint attempt,
  including failed attempts. It attaches one opaque workflow ID to client
  requests and preserves existing latest-response compatibility fields.
- The server correlates responses and runtime traces with request, workflow,
  and client-attempt IDs. Success traces persist structured local/frontier
  usage and retry details without prompt or output text. Error traces mark
  accounting unknown when the amount of work cannot be reconstructed.
- Local attempt usage is accepted only when its aggregate count agrees with
  the reported local model-call count. Frontier usage must likewise reconcile
  with its call count before token usage is marked complete. Inconsistent
  frontier totals are unknown, and missing cost is reported separately from
  missing token usage.
- Client retry aggregation requires correlated, distinct request IDs and
  reconciles each workflow total against its local and frontier subtotals.
  Attempt-level nested usage is allowlisted to accounting fields and token
  counters.
- Canary token aggregation requires the versioned receipt schema, unique
  request IDs, call-count consistency, and token-total reconciliation.
- The canary keeps absent or incomplete token totals unknown rather than
  silently adding zero. Local model tokens and raw-input estimates are separate.

## Evidence boundary

This is receipt completeness work, not a measured utility result. No test,
inference, provider call, benchmark, or paired canary was run for this phase.
Static inspection and `git diff --check` are the only checks performed here.
The active Gate D scorer remains fail-closed and net savings remain
unestablished. Cost, correction, verifier, and task-outcome coverage are still
needed before an accounting-complete canary can pass.

Phase 452 adds partial local usage receipts for generation exceptions and
retains them through upstream fallback errors. Delivery status can still
diverge from a persisted success trace if a client disconnects after trace
writing. See [Phase 452](../phase-452-partial-local-usage-accounting/README.md);
the canary continues to treat incomplete outcomes as unknown.

The Phase448 capture audit found a useful candidate workload source, but
prompt/context fields remain uninspected. The user replied "full approval, go
ahead" but supplied no new trace path or consent/license receipt. Treat this
as owner authorization only. It does not establish third-party consent or
resolve the audit's email-shaped privacy flags. Keep the raw capture untouched
pending that review and any required trace joins.
