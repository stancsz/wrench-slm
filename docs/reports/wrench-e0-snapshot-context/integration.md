# E0 exact snapshot to ContextLedger bridge

Job: `W2-E0-SNAPSHOT-CONTEXT-20260924`
Nonce: `SCX-6f3a9`
Baseline: `ee9bf186ef8c72f33ab614a93d74dae5bcd248a1`

## Implementation

`src/wrench_harness/snapshot_context.py` exposes
`admit_snapshot_source(root=..., snapshot=..., path=..., ledger=...,
source_order=...)`. It calls `retrieve_exact` first and maps its verified
statuses to explicit bridge outcomes. Changed sources become `STALE`; unknown
snapshot/source, missing, and unsafe results remain distinct. Exact bytes must
decode as strict UTF-8 and produce non-empty text before the bridge calls
`ContextLedger.add_segment`.

Successful admissions use a deterministic segment ID derived from snapshot
SHA-256, normalized source path, and verified content SHA-256. Metadata binds
the same snapshot/path/content identities. Receipts contain no source bytes.
`ContextAdmissionError` becomes `CONTEXT_REJECTED` with its reason. Retrieval,
text decoding, and context rejection tests confirm no ledger mutation on
failure.

The bridge performs no scan, persistence, pinning, model/provider call, or
context selection. Token counts use the ledger's existing counter behavior;
admission does not guarantee fit in a later active prompt budget.

## Verification

Focused command, with `TEMP`, `TMP`, and `TMPDIR` set to
`C:\wrench-slm-data\tmp\W2-E0-SNAPSHOT-CONTEXT-20260924`, bytecode disabled,
and the preinstalled pytest dependency path on `PYTHONPATH`:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest tests/test_snapshot_context.py
```

Result: `7 passed`. The first invocation without `PYTHONPATH` could not import
pytest; the successful run used the existing dependency directory and installed
nothing. Scoped `git diff --check` passed. Final storage status was
`WITHIN_LIMIT`: actual 590,307,774 bytes, active reservation 20,000,000 bytes,
projected 610,307,774 bytes, no checker errors. C: had 186,319,204,352 bytes
free. No commit was created.

## Independent review

Job `W2-E0-SNAPSHOT-CONTEXT-REVIEW-20260924`, nonce `SCXR-4b8c10`, reviewed
the implementation, tests, and report against the existing snapshot and
context contracts. The reviewer accepted the slice with no blocking findings
for identity binding, failure atomicity, status mapping, or storage and
authority boundaries. The reviewer did not rerun tests. E0 remains incomplete.
