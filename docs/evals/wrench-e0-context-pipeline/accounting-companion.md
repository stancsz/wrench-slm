# E0 preparation accounting companion review

Historical v1 evaluation for the initial deterministic-counter projection.
The current canonical accounting schema is v2 and includes
`artifact_pin_scope_duration_ns`; see the [pin-scope accounting join
evaluation](pin-scope-accounting-join.md). This record remains as evidence for
the earlier v1 slice.

Date: 2026-09-24 (America/Edmonton)
Status: accepted as a bounded component slice; not E0 milestone acceptance.

## Scope and revision

Reviewed the accounting companion added to
`src/wrench_harness/e0_context_pipeline.py`, its focused tests, and the E0
pipeline goal/report. The implementation was based on `52438e2`; the commit
containing this review records the reviewed code and tests. Owner-edited
`docs/northstar/*` files were not part of this change.

## Critique and verification

The companion improves reproducibility for facade-owned preparation counters:
it uses canonical versioned JSON, a fixed v1 field projection, a preparation
hash join, and an independent digest. It excludes nondeterministic elapsed
time and keeps unmeasured dimensions null. The public verifier enforces a
bounded input before parsing, checks canonical form and exact v1 keys/types,
and confirms the digest and preparation join. It establishes data integrity,
not measurement authenticity, callback completeness, or authorization.

Two independent read-only reviewers requested changes during review. The
implementation repaired both findings: oversized/deep verifier inputs now
fail closed before parsing, and structural candidate count stays null until a
query result exists. A successful query with no matches records zero. Final
review by `accounting_evidence_audit` and `integrated_api_contract_audit`
confirmed those repairs. `goal_traceability_audit` recommended tracking the
slice under the E0 caller-owned pipeline goal; that tracking was corrected.

Focused Windows verification used Python 3.11.16 and the existing cached
pytest 8.4.2 path:

- `tests/test_e0_context_pipeline.py`: **8 passed**.
- `git diff --check`: passed.
- The storage checker ended `WITHIN_LIMIT`, with no active reservations and
  590,894,282 bytes counted across configured Wrench roots.

The run covers repeatability, hash verification, elapsed-time exclusion,
null-versus-zero, stale sources, prompt rejection, serializer failure, store
failure, invalid input, malformed/oversized/deep payloads, and strict v1
shape. An intermediate test edit misplaced a block; that run failed with a
`NameError`, the test was corrected, and the final focused run passed.

## Remaining E0 gaps

This companion covers facade call sites only. Callback effects, provider and
client lifecycle, exact OpenCode serialization/tokenization, active
session/worktree root binding, end-to-end authority, and some resource
dimensions remain unobserved. The receipt is optional when no aggregate
preparation hash exists, is not persisted or exported, and is not included in
the outcome receipt. Hashes can link repeated inputs and are not authentication
or anonymization. POSIX pytest, OpenCode installation/execution, and real
matched-task outcomes were not tested.

Accordingly this slice is accepted locally as useful E0 preparation-accounting
evidence. The experiment's complete baseline-accounting, authority, and
runtime-integration criteria remain open; E4 utility still requires consented
matched real tasks and a reviewed outcome oracle.
