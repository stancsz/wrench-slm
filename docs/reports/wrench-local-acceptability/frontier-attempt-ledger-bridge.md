# Offline frontier attempt ledger bridge

Status: bounded converter implemented and checked with synthetic in-memory
fixtures. No provider, client, model, task corpus, or saved usage ledger was
accessed.

`wrench_harness.frontier_attempt_ledger_bridge.bridge()` accepts
`wrench.frontier-attempt-ledger.v1` and produces the existing
`wrench.paired-frontier-savings-input.v1` shape. Each task carries a source
snapshot digest and baseline/Wrench arms. Each arm names its run and context
receipt, explicitly declares `route: frontier` and zero local model, tool,
and verifier calls, lists frontier calls in attempt order, and supplies usage
rows keyed by call ID. Every attempt must also name the frontier route and
must not be a fallback or `not_run` row. Unknown outcomes are rejected. The
comparison pins protocol, client, frontier model, and token convention
identities.

This schema covers only frontier-only arms. It is not usable for Wrench SLM,
local-model, tool-using, verifier-using, fallback, or mixed-route workflows
until the ledger and accounting contract are explicitly extended for those
calls. Declared call counts are checked, not inferred from omissions.

The converter requires exact nonnegative input and output token counts and
known nonnegative cost microunits for every frontier call before constructing
a complete receipt. It binds rows to attempt IDs, rejects duplicate task or
attempt IDs, and records duplicate, unmatched, missing, malformed, non-exact,
or wrong-counter usage as an incomplete arm. If any arm usage is incomplete,
all usage for that arm remains unknown; the existing receipt validator and
paired reporter exclude that pair. Failed task outcomes remain attached to
valid complete receipts and are counted separately by the reporter.

The converter delegates canonical receipt construction and validation to
`build_outcome_receipt()` and `validate_outcome_receipt()`. It does not
reimplement savings arithmetic. Feed its JSON output to
`tools/report_paired_frontier_savings.py` for validation, exclusions, and
aggregation. The two functions do not authenticate telemetry, establish
prompt parity, or verify outcome truth; this bridge creates no measured
utility or savings evidence by itself.

CLI stream contract: on success, stdout contains exactly one JSON document in
the paired-frontier-savings input schema, ready for the existing reporter.
Stderr contains exactly one JSON audit record with schema
`wrench.frontier-attempt-ledger-bridge-audit.v1` and per-task/per-arm status
and exclusion reasons. The audit record is capped at 256 KiB. Consumers may
pipe stdout directly into the paired reporter while retaining stderr for
diagnostics. On input or output-bound errors, the CLI returns status 2 and
prints one JSON error object to stdout; there is no successful paired-input
document in that case. The CLI reads at most 1 MiB plus one byte before
rejecting an oversized input, so the size check does not buffer an unbounded
file.

Focused stdlib `unittest` checks cover an exact two-arm conversion, failed
outcomes, missing/duplicate/unmatched usage, wrong token convention,
token-only and missing-cost exclusion, duplicate task identity, nonzero or
omitted local/tool/verifier call declarations, non-frontier routes, fallback
calls, `not_run` attempts, and unknown outcomes. All checks use synthetic
in-memory fixtures. A captured CLI test checks parseable reporter JSON on
stdout and the missing-usage reason in the single stderr audit record. The
broader pytest suite was not run because pytest is unavailable in the current
Python environment.
