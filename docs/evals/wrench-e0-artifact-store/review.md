# E0 bounded artifact store review

## Decision

Accept this standalone persistence increment with explicit concurrency and
durability limits. The store binds caller-supplied bytes to asserted snapshot,
source-path, and content identities, verifies exact reads, supports bounded
request-local pins, and reports missing, evicted, or corrupt handles.

This does not complete E0, qualify a production store, or authorize downloads,
model inference, training, spending, publication, or deployment.

## Scope and review

- Baseline: `36d2d1d89bd4eb3036a3bb2874866fff517d5900`.
- Implementation: `src/wrench_harness/artifact_store.py`.
- Tests: `tests/test_artifact_store.py`.
- Handoff: `docs/reports/wrench-e0-artifact-store/store.md`.
- Independent review: accepted after repairs for staging-slot enforcement,
  malformed-manifest recovery, and symlink/reparse validation across the store
  root chain.

## Verification

Windows Python 3.11 focused pytest result: **19 passed, 3 skipped**. The skipped
tests require symlink creation privileges unavailable to this Windows account.
The test scratch path was under `C:\wrench-slm-data\tmp\W2-E0-ARTIFACT-STORE-20260924`.

An existing Ubuntu 24.04 WSL Python 3.12 standard-library smoke check passed
symlinked-ancestor rejection without creating a redirected store, exact object
read, and store reopen. A prior bounded WSL smoke also verified request-pin
eviction blocking and restoration of a valid previous manifest. No packages
were installed; temporary fixtures were removed.

`git diff --check` passed. Before commit, storage status was `WITHIN_LIMIT`:
590,258,742 actual bytes plus the 32,000,000-byte reservation, below the
50,000,000,000-byte ceiling. C: had more than 5 GB free.

## Limits

- The store validates the bytes and hashes supplied by its caller. It does not
  independently prove that a snapshot/path pair came from `SourceSnapshot`.
- Use one `ArtifactStore` instance per root. Locks and pins are instance-local;
  multiple processes and external writers are unsupported.
- Root components are checked with `lstat` before store use, but directory
  handles are not pinned across the path walk. Callers must prevent concurrent
  namespace replacement in the root chain.
- Previous manifests share the same volume. Atomic replacement and file
  `fsync` do not prove directory-entry or power-loss durability, and do not
  protect against volume loss.
- This primitive is not yet connected to snapshots, context assembly, client
  requests, retention scheduling, or the production runtime.

## Next E0 work

Run the focused tests on a POSIX host when pytest is available. Then integrate
snapshot-backed handles with the context compiler and continue the remaining
E0 requirements: namespace discovery, exact final serialized-prompt
accounting, and outcome receipts. Keep E1-E4 gates open.
