# E0 snapshot identity and exact-source retrieval review

## Decision

Accept this bounded E0 implementation increment.
The implementation reads caller-selected sources through platform-specific
handle-relative walks and returns bytes only when the admitted size and SHA-256
still match. POSIX pytest fixtures now pass on the existing Ubuntu 24.04 WSL
runtime.

This review does not complete E0, qualify production behavior, or authorize
model downloads, inference, training, spending, publication, or deployment.

## Scope and evidence

- Baseline: `380c799f3199e08404908ecd6f7faa7496992367`.
- Implementation: `src/wrench_harness/snapshot.py`, exported through
  `src/wrench_harness/__init__.py`.
- Tests: `tests/test_snapshot.py`.
- Handoff report: `docs/reports/wrench-e0-snapshot-retrieval/source-snapshot.md`.
- Independent review found no remaining blocker after the root-acquisition
  repair. Earlier Windows path-alias, reparse-point, malformed-handle, and
  POSIX root-ancestor findings were repaired and re-reviewed.

## Verification

Windows command, Python 3.11:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider tests/test_snapshot.py
```

Result: **18 passed, 4 skipped**. The skipped cases are three POSIX-only tests
and a symlink fixture that the Windows host could not create. Native Windows
handle-walk, path-alias, and deterministic reparse-bit checks ran.

On Ubuntu 24.04 WSL (Python 3.12.3), the existing cached pytest 8.4.2 and
pluggy 1.6.0 packages were mounted from the approved data root; no packages
were installed. `tests/test_snapshot.py` completed with **20 passed, 2
skipped**; `tests/test_artifact_store.py` completed with **22 passed**. The
snapshot skips are the Windows case-alias and native Windows handle-walk tests.
`PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` kept test artifacts out
of the source tree. Earlier bounded standard-library smoke checks also passed
exact nested POSIX retrieval, final-component symlink replacement rejection,
and root-ancestor symlink replacement immediately before root-chain
acquisition.

```powershell
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=/mnt/c/Users/stanc/github/wrench-slm/src:/mnt/c/wrench-slm-data/cache/wrench-v2-test-deps-20260923/site-packages python3 -B -m pytest -p no:cacheprovider tests/test_snapshot.py tests/test_artifact_store.py
```

`git diff --check` passed. Public package exports imported successfully. For
the POSIX pytest run, storage admission job
`W2-E0-POSIX-PYTEST-20260924` reserved 20,000,000 bytes. The checker reported
`WITHIN_LIMIT` at 590,932,348 actual bytes plus that reservation; the
reservation was released after the test process stopped and its final files
were accounted for.

## Review notes and limits

- Source selection is explicit and finite. There is no recursive discovery,
  persistent source copy, index, cache, model, or provider integration.
- The v2 manifest and snapshot hash bind content/path identity to the
  normalized configured root path. They do not identify a physical directory,
  persist a durable root registration, or survive restart as a registered
  handle.
- Windows traversal pins the caller-selected root and each child handle, opens
  reparse points without following them, and denies write/delete sharing during
  the bounded read. Initial root resolution and filesystem sharing semantics
  remain trusted platform boundaries.
- POSIX traversal starts at `/` and uses pinned directory descriptors,
  `O_DIRECTORY`, and `O_NOFOLLOW` for root and child components. It uses
  nonblocking final opens and post-read binding/hash checks. POSIX does not
  prevent writes through preexisting descriptors, so detected mutation fails
  closed and hash mismatch never returns bytes. POSIX pytest fixtures were
  verified by the WSL run above.
- No power-loss durability, artifact retention, root discovery, request-lifetime
  pinning, namespace discovery, exact serialized-prompt accounting, or outcome
  receipts are implemented in this increment.

## Remaining limits

The manifest is an in-memory value, not a durable handle registry or a
persistent artifact store. Its v2 digest binds the normalized lexical
configured root path, but does not identify a physical directory.
Runtime-matched prompt/tokenizer identity, complete lifecycle accounting,
and end-to-end authority evidence remain open E0 work. Matched-task utility
across the three clients is an E4 gate. Keep E1-E4 and production claims open
until their evidence exists.
