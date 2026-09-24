# E0 configured-root snapshot binding review

## Decision

Accept this bounded v2 snapshot identity increment. The manifest digest now
includes the normalized lexical absolute configured-root path hash. Exact
retrieval checks the same identity before reading and continues to recheck
exact source size and content hash.

This slice does not complete E0, qualify production behavior, or authorize
model downloads, inference, training, spending, publication, or deployment.

## Independent review

The read-only review found no blocking correctness issue in creation/retrieval
normalization, cross-root rejection, schema validation, or legacy failure
behavior. The review confirmed that the binding is only a configured-path
consistency check: it is neither physical-directory identity nor
authentication. Byte-identical replacement at the same path still matches,
callers can recompute public hashes, checkout moves invalidate old snapshots,
and unsalted path digests can be dictionary-tested.

## Verification

- Final Windows Python 3.11.16 run: **115 passed, 7 skipped** across snapshot,
  artifact-store, context bridge, structural index, context pipeline, and
  outcome receipt suites. POSIX-only cases and unavailable symlink fixtures
  were skipped.
- Final Ubuntu 24.04 WSL Python 3.12.3 run: **120 passed, 2 skipped** across the same
  suites. Only Windows-specific path alias and native handle-walk cases were
  skipped.
- Both test invocations used `PYTHONDONTWRITEBYTECODE=1` and disabled pytest
  cache writes. Temporary fixtures were directed to the approved data root.
- `git diff --check` passed.
- Storage checker admitted job `W2-E0-ROOT-BOUND-FINAL-20260924` with a
  50,000,000-byte reservation and reported `WITHIN_LIMIT` during the run.
- Four Windows and WSL fixture trees remain under `C:\\wrench-slm-data\\tmp`;
  their combined inventory is 1,953 files and 20,008,338 bytes, counted by
  the storage checker.

The serializer/tokenizer identity, dispatch-veto authority, full lifecycle
accounting, outcome oracle, and E4 matched-task utility remain open gates.
