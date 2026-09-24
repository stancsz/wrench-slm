# E0 snapshot identity and exact-source retrieval review

## Decision

Accept this bounded E0 implementation increment with a verification caveat.
The implementation reads caller-selected sources through platform-specific
handle-relative walks and returns bytes only when the admitted size and SHA-256
still match. POSIX pytest fixtures remain to be run on a POSIX host; bounded
WSL standard-library smoke checks passed on this host.

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

An existing Ubuntu 24.04 WSL Python 3.12 runtime has no pytest installed. No
packages were installed. A bounded standard-library smoke check passed exact
nested POSIX retrieval, final-component symlink replacement rejection, and
root-ancestor symlink replacement immediately before root-chain acquisition.
Its temporary fixture files were removed.

`git diff --check` passed. Public package exports imported successfully. The
storage checker reported `WITHIN_LIMIT`: 589,355,857 actual bytes plus the
20,000,000-byte active reservation, below the 50,000,000,000-byte ceiling.

## Review notes and limits

- Source selection is explicit and finite. There is no recursive discovery,
  persistent source copy, index, cache, model, or provider integration.
- The manifest and snapshot hash are in-memory content/path identity. They do
  not bind a durable root identity or survive restart as a registered handle.
- Windows traversal pins the caller-selected root and each child handle, opens
  reparse points without following them, and denies write/delete sharing during
  the bounded read. Initial root resolution and filesystem sharing semantics
  remain trusted platform boundaries.
- POSIX traversal starts at `/` and uses pinned directory descriptors,
  `O_DIRECTORY`, and `O_NOFOLLOW` for root and child components. It uses
  nonblocking final opens and post-read binding/hash checks. POSIX does not
  prevent writes through preexisting descriptors, so detected mutation fails
  closed and hash mismatch never returns bytes. POSIX pytest fixtures remain
  unverified on a native POSIX host.
- No power-loss durability, artifact retention, root discovery, request-lifetime
  pinning, namespace discovery, exact serialized-prompt accounting, or outcome
  receipts are implemented in this increment.

## Next action

Run the POSIX pytest fixtures on a POSIX host, then continue the deterministic
E0 baseline with the bounded reversible artifact store and remaining E0
requirements. Keep E1-E4 and production claims open until their evidence exists.
