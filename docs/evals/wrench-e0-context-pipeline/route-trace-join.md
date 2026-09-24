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

## Route-preparation binding follow-up

**Decision:** Pass for this bounded trace-binding slice; not an E0 acceptance.
The source requires a successful route-preparation receipt for completed route
evidence and requires its exact preparation object in the OpenCode join. The
emitted trace schema is v3 and records the route-preparation receipt digest.

**Verification:** `tests/test_e0_lifecycle_accounting.py`: **14 passed** on
Windows Python 3.11.16 using the existing cached pytest runtime. The initial
run found one fixture snapshot mismatch; after fixing that fixture, the rerun
passed. No packages were installed. `git diff --check` passed. Storage stayed
`WITHIN_LIMIT`; the test reservation was released after accounting for the
pytest scratch directory under the approved data root.

**Independent review:** PASS, no blocking findings, on job
`W2-NS-E0-TRACE-ROUTEPREP-FINAL-REVIEW-20260925`, nonce
`TRPLINK-FINAL-REV-C91B`. The review was read-only and did not rerun tests.
It verified the tests exercise preparation object identity, rejection of a
standalone completed route, same-snapshot path/content mismatch, and a
tampered receipt.

The result remains a structural join over caller-supplied records. It does not
authenticate route execution or establish dispatch enforcement, runtime
parity, task truth, or full E0 acceptance.
