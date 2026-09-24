# Artifact-store migration and recovery regression evaluation

## Decision

Accept the focused regression additions as evidence for the bounded store's
legacy retention normalization, shared-blob eligibility, unreachable-target
no-op behavior, and manifest recovery ordering. This evidence does not qualify
power-loss durability or complete the E0 request lifecycle.

## Review

- Job: `W2-NS-ART-RECOVERY-TEST-20260924`.
- Nonce: `ARTREC-6F20`.
- Base: `a5dba0f`.
- Changed code: `tests/test_artifact_store.py` only.
- Independent reviewer: `/root/artifact_recovery_test_supervisor/test_review`.
- Result: **PASS**, no findings. The reviewer verified that unchanged-state
  snapshots include staging entries and that the in-commit interruption case
  fails after replacing the previous slot but before replacing the current
  slot, matching recovery assertions to the implementation.

The review was read-only and did not execute tests. It evaluated the final
test diff against `src/wrench_harness/artifact_store.py`.

## Verification

Windows Python 3.11.16 and cached pytest 8.3.5 ran only
`tests/test_artifact_store.py`: **26 passed, 3 skipped**. Existing symlink
cases were skipped because this account cannot create those links.
`git diff --check` passed. Test temporary files were placed under
`C:\wrench-slm-data\cache\W2-NS-ART-RECOVERY-TEST-20260924`. No packages were
installed.

## Limits

The injected exceptions establish ordering and recovery behavior at Python
call boundaries. They do not simulate actual power loss, torn writes, directory
entry persistence, multi-process races, or volume failure. The store still
uses process-local pins and same-volume manifests. Production retention policy,
failure-independent backup and full E0 lifecycle qualification remain open.

See the [test evidence report](../../reports/wrench-e0-artifact-store/recovery-regressions.md)
and [artifact-store goal](../../goal/wrench-e0-artifact-store/GOAL.md).
