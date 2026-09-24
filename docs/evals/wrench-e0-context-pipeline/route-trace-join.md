# E0 rule-route partial trace join evaluation

## Decision

Accept as a bounded, optional structural join from a snapshot-bound
rule-route result into partial lifecycle trace schema v2, subject to the
caller-supplied provenance limitations below. This is not complete E0
accounting or an outcome claim.

## Verification

Windows Python 3.11.16 with pytest 9.1.1 ran
`tests/test_e0_lifecycle_accounting.py` and `tests/test_e0_rule_route.py` after
the reviewer-requested sanitization: **41 passed**. `git diff --check` passed.
Storage admission, post-test status, and post-release status were
`WITHIN_LIMIT`; the report records byte counts, release, and the shared uv
cache included in the inventory.

## Review

The initial independent read-only review requested changes because arbitrary
caller-controlled action/reason/evidence-status strings could enter the
summary. The implementation now hashes paths and maps unknown action, reason,
and status values to a fixed `other` label. The second read-only review passed
the scoped diff with no remaining blockers (`W2-NS-E0-ROUTE-RECEIPT-FINAL-REVIEW2-20260924`,
nonce `RTE-REV2-6B90`). It did not edit files or run tests.

## Limits

The route result, snapshot identity, and outcome receipt are caller-supplied
and unauthenticated. Summary counters are caller-reported component counters.
The join does not authenticate invocation or prove user intent, dispatch veto,
task truth, provider behavior, runtime resources, consent, or customer utility.
It copies no route observation text or raw source paths into the trace; paths
are represented by hashes.

See the [implementation report](../../reports/wrench-e0-context-pipeline/route-trace-join.md)
and [goal](../../goal/wrench-e0-context-pipeline/GOAL.md).
