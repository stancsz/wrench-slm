# Success-qualified frontier savings metric

Goal: [Wrench local work acceptability](../../goal/wrench-local-acceptability/GOAL.md)
Worker: root orchestrator
Status: **implemented and focused-checked; no observed savings pairs**
Date: 2026-09-26

## Change

The paired frontier reporter now emits two separate metrics:

- The existing all-exact-usage arithmetic mean and ratio-of-sums remain a
  diagnostic that includes failed and unverified outcomes.
- The new `average_per_successful_task_savings_percent` and
  `ratio_of_sums_successful_task_savings_percent` include a task only when
  both arms have exact frontier-token usage, the same task/snapshot and frozen
  comparison identity, a nonzero baseline, completed outcomes, independently
  verified provenance, and a passed verifier. Existing receipt validation
  requires the verifier identity and evidence references. These are
  structurally validated receipt declarations, not authenticated outcome
  truth.

Each per-task row identifies success-metric eligibility and, when excluded,
the reason. `successful_pair_count`, token totals, and success-metric exclusion
counts are explicit. Exact tokens with unknown costs remain eligible for the
token-only metric and are counted separately. The output schema is now v3.

## Verification

- 18 non-`pytest.raises` reporter test functions were directly invoked under
  Python 3.13 and passed. This includes both-arm success, verified failures,
  unverified completions, one-sided verifier failure, unknown token usage,
  exact usage with unknown cost, snapshot mismatch, and zero baseline.
- The duplicate-task and invalid-comparison exception boundaries were also
  invoked directly and rejected their inputs as expected.
- All 12 standard-library tests in
  `tests/test_frontier_attempt_ledger_bridge.py` passed, confirming the bridge
  still feeds the reporter after its output-schema update.
- `python -m py_compile tools/report_paired_frontier_savings.py` passed.
- `git diff --check` passed.
- `python -m pytest tests/test_report_paired_frontier_savings.py -q` could not
  run because pytest is not installed. Two exception-assertion functions were
  therefore not run by pytest; their equivalent rejection behavior was
  checked directly.
- An independent read-only review found no logic defect and prompted the
  one-sided verifier and unknown-cost regression cases added above.

## Result and limits

This change makes the requested success-qualified arithmetic explicit; it
does not create matched usage data. No actual task receipts were processed,
and no provider, client, model, or local endpoint was called. Both the all-
usage real-world result and the success-qualified real-world result remain
**N/A**, with zero eligible pairs. Receipt hashes and provenance values are
structural checks; they do not authenticate client telemetry, task truth,
prompt parity, or protocol compliance.

The next production-directed blocker remains an authorized full-lifecycle
capture path that binds actual downstream dispatch and usage, retries,
fallbacks, local processing, and independently verified outcomes to the same
matched task. Current authority does not permit provider traffic, client
execution, or real-task capture.
