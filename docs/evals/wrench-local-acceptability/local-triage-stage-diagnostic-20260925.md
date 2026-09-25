# Evaluation: local log-triage stage diagnostic

Status: **PASS after repair for receipt reconciliation; FAIL for local SLM
triage on this exposed two-case diagnostic.** This does not accept a semantic
task class.

- Goal: [Measure acceptable local work](../../goal/wrench-local-acceptability/GOAL.md)
- Diagnostic report: [stage results](../../reports/wrench-local-acceptability/local-triage-stage-diagnostic-20260925.md)
- Independent reviewer: `/root/screen_runtime_review`
- Review job: `W2-LOCAL-TRIAGE-DIAGNOSTIC-REVIEW-20260925`, nonce `LTDR-6BE2`
- Revision reviewed: `3c9cb277a311e705e225c9322fd3f0d6bdd3ff2f`

The reviewer recomputed the canonical manifest digest and receipt hashes from
the saved files and joined exactly `triage-a` and `triage-b` across the two
receipts. The initial draft incorrectly mapped literal exception names to
normalized categories. Following the review finding, the corrected report
derives the actual oracle answers `TypeError` and `ValueError` from observed
log lines using the fixture's `log_error_type` rule. The manifest identity
matched both receipts. The deterministic operation rows passed exact route
and executor observation checks on 2/2 cases. The local SLM rows had zero
required tool calls, invalid schema, ungrounded/incorrect outcomes, and no
case passes (0/2).

The comparison is valid only as a retrospective diagnostic join. The
deterministic route's explicit-read instruction differs from the SLM's
semantic triage prompt, and its executor returns source bytes rather than a
final error classification. The deterministic rows are operation passes, not
completed triage tasks. The source fixture was exposed, so these cases cannot
serve as held-out acceptance or tuning data. No model, client, provider,
training process, or external service was run. Frontier savings remain N/A
with zero matched usage pairs.

No acceptance claim extends beyond the recorded synthetic mechanics. A fresh
holdout and independent tool-grounded outcome oracle remain required before
any semantic local SLM class can be accepted.

The original derivation-label defect was repaired in the linked report and
this evaluation. It did not change the receipt identity, operation results,
SLM scores, or scope decision.
