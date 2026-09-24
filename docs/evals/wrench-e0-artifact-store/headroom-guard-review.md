# Artifact-store physical-volume headroom guard evaluation

## Decision

Accept the cooperative per-write physical headroom check for bounded local
ArtifactStore staging writes. Do not treat it as a hard 5 GB volume guarantee
or as a replacement for the separate 50 GB aggregate storage admission.

## Review

- Job: `W2-NS-STORE-HEADROOM-20260924`.
- Nonce: `SPACE-7D2A`.
- Base: `45162350068eaf6541e15b1eec5dca995b1c0559`.
- Changed implementation and tests: `src/wrench_harness/artifact_store.py`,
  `tests/test_artifact_store.py`.
- Independent reviewer: `/root/artifact_store_headroom_gate/store_headroom_review`.
- Review result: **NEEDS_CHANGES** for any claim of a hard 5 GB guarantee. The
  review found that sequential object and manifest writes recheck projected
  staging bytes plus the 5 GB reserve, fail closed on probe errors, and leave
  reads unchanged. It identified a time-of-check/time-of-use race with other
  store roots or processes and noted that initial directory creation precedes
  the first manifest probe. This evaluation narrows the claim to a cooperative
  per-write guard and records both limitations. The reviewer made no edits and
  ran no tests.

## Verification

Windows Python 3.11.16 and cached pytest 8.3.5 ran
`tests/test_artifact_store.py`: **33 passed, 3 skipped**. Existing symlink
fixtures were skipped because this account cannot create those links. The
final run included the constructor fallback adjustment. The
[headroom guard report](../../reports/wrench-e0-artifact-store/headroom-guard.md)
records the test command and storage/RAM/VRAM admission snapshot.

## Limits

The implementation checks current free space before each bounded staging
write. It does not reserve physical capacity across a transaction, coordinate
with external writers, or prove power-loss durability. Initialization creates
the store directories before the first guarded manifest write. The separate
50 GB cooperative aggregate budget remains independently enforced by the
operator.
