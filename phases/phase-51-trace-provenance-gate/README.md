# Phase 51: approved-trace provenance gate

The matched workflow evaluator now requires more than an authorization string
before it computes savings. An approved manifest must include a 64-character
trace-set SHA-256 and non-empty capture ID, UTC capture time, reviewer, and
source-scope metadata. Missing provenance returns `BLOCKED_TRACE_PROVENANCE`
with no paired savings result.

This prevents an unreviewed or unverifiable fixture from being presented as a
real-workflow result. No real trace data was added.
