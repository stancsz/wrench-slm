# Evaluation: success-qualified frontier savings metric

Date: 2026-09-26
Revision base: `7956a77905c4dbb5845ae500d6ebe1a5d525fd1a`
Author/reviewer: root implementation; independent read-only subagent review

## Question

Does the reporter's requested successful-task mean exclude failed or
unverified pairs while retaining an explicitly labeled all-usage diagnostic?

## Inspection and checks

The implementation was reviewed in
`tools/report_paired_frontier_savings.py`, with receipt semantics checked in
`src/wrench_harness/outcome_receipt.py`. The independent reviewer confirmed
that task, snapshot, comparison, exact usage, and nonzero baseline checks occur
before success qualification. Both arms must have `completed` status,
`independently_verified` provenance, and verifier result `passed`. The receipt
validator additionally requires verifier identity and evidence and consistent
outcome/verifier status. Those fields remain caller-supplied declarations.

The legacy arithmetic metric includes all exact-usage pairs and is labeled as
a diagnostic, including failed tasks. The new mean and ratio-of-sums have
separate pair counts, totals, per-task eligibility, and exclusion reasons.
Token-complete receipts with unknown costs remain eligible for token savings.

Focused verification passed: 18 directly invoked reporter test functions,
two direct exception-boundary checks, 12 standard-library bridge tests,
Python compilation, and `git diff --check`. The normal pytest command was
unavailable because the environment has no pytest module.

## Decision

**Metric logic accepted for bounded offline use.** This is a software
accounting improvement, not a savings result. There are still zero actual
matched usage pairs. Hashes validate receipt structure only; actual dispatch
telemetry, prompt parity, and outcome truth remain unauthenticated. No client,
provider, model, local endpoint, or real workflow was used.
