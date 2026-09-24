# E0 exact snapshot, artifact store, and context roundtrip

Job: `W2-E0-SNAPSHOT-ARTIFACT-ROUNDTRIP-20260924`  
Nonce: `SAR-8d02ce`  
Baseline: `103f6bd440c819e1df3f23be9b901705fa013422`

## Implementation

`src/wrench_harness/snapshot_artifact_context.py` exposes
`admit_snapshot_artifact_source(source_root=..., snapshot=..., path=...,
store=..., ledger=..., source_order=...)`. It retrieves and verifies the
current source first. Only successful exact bytes are passed to `ArtifactStore.put`
with snapshot, normalized path, and content hashes. It verifies the returned
handle identity, pins it with `store.request()`, reads it again within that
scope, and checks both exact bytes and SHA-256 before strict UTF-8 decoding and
ledger admission.

Receipts return status, segment ID, source identities, and artifact handle ID,
but no source bytes. Retrieval misses are distinct from store errors, explicit
artifact missing/evicted/corrupt outcomes, roundtrip mismatches, non-text, and
context rejection. Source retrieval failures do not write artifact objects.
If context admission fails after a verified roundtrip, the content object
remains in the caller's store; the bridge does not delete it. The ledger remains
unchanged.

No scan, model/provider call, inference/training, package install, or commit is
part of this slice. Store roots remain caller-owned; ArtifactStore concurrency
and recovery limitations remain in force.

## Verification

Focused Windows command used Python 3.11 with `TEMP`, `TMP`, and `TMPDIR` set
to `C:\wrench-slm-data\tmp\W2-E0-SNAPSHOT-ARTIFACT-ROUNDTRIP-20260924`,
`PYTHONDONTWRITEBYTECODE=1`, pytest plugin autoload disabled, and the existing
pytest dependency path on `PYTHONPATH`:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest tests/test_snapshot_artifact_context.py
```

Result: `12 passed`. The independent review requested coverage for bounded
store-write failure and roundtrip identity mismatch; both cases were added and
passed on the follow-up run. Scoped `git diff --check` passed. Final storage
status after the follow-up run was `WITHIN_LIMIT`: actual 590,354,454 bytes,
active reservation 20,000,000 bytes, projected 610,354,454 bytes, no checker
errors. C: had 186,317,910,016 bytes free. No commit was created.

## Independent review

Job `W2-E0-SNAPSHOT-ARTIFACT-ROUNDTRIP-REVIEW-20260924`, nonce `SARR-31b0a6`,
accepted the implementation with a non-blocking request for the two typed
error cases described above. The reviewer confirmed identity binding, exact
roundtrip checks, failed-admission ledger behavior, and scope limits. The
follow-up test run used the preinstalled dependency path under the approved
cache root; no packages were installed. E0 remains incomplete.
