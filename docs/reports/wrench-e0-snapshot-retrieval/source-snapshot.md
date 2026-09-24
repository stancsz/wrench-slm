# E0 source snapshot implementation handoff

Job: `W2-E0-SNAPSHOT-20260924`

Nonce: `SNAPSHOT-58c912`

Repair job: `W2-E0-SNAPSHOT-REPAIR-20260924`

Repair nonce: `SNAPREPAIR-60a31f`

Reparse repair job: `W2-E0-SNAPSHOT-REPARSE-20260924`

Reparse repair nonce: `REPARSE-127d4a`
Baseline: `380c799f3199e08404908ecd6f7faa7496992367`

## Delivered

`src/wrench_harness/snapshot.py` implements a caller-enumerated, in-memory
source manifest and exact-byte retrieval. Paths are normalized to `/`, sorted
before hashing, and bound to byte size and SHA-256. Admission rejects absolute
and parent paths, duplicate normalized paths, symlinks and reparse points,
non-regular files, more than 256 files, files over 256 KiB, and selected
content over 4 MiB. A 1,024-character path limit is checked before path
normalization. Retrieval returns bytes only for a matching admitted path after
rechecking file identity, size, metadata, and digest. It reports explicit
unknown-snapshot, unknown-source, missing, changed, and unsafe statuses. No
source copy, index, or cache is written. No default scan or model/provider
integration is present.

On Windows, case-folded aliases are duplicate paths. ADS colon syntax and
trailing-dot/space components are rejected. Reparse attributes are checked on
roots, path components, and opened file descriptors. The Windows reader opens
the explicit root with `CreateFileW`, then opens each child with native
`NtCreateFile` using the pinned parent handle as `RootDirectory` and
`FILE_OPEN_REPARSE_POINT`. Root and directory handles remain open with sharing
that denies write/delete access while the bounded file read is in progress.

On POSIX, root acquisition starts at `/` and opens every root component
relative to its pinned parent with `O_DIRECTORY` and `O_NOFOLLOW`. Source
components use the same parent-relative walk. The final component opens with
`O_NOFOLLOW` and `O_NONBLOCK`, is validated with `fstat`, and remains open
through the bounded read and binding rechecks. Root and source component
bindings are rechecked before returning. Missing `dir_fd`, no-follow,
directory, or nonblocking primitives fail closed. Every opened descriptor is
closed in a `finally` path. Both implementations validate public snapshot
shape, canonical paths, bounds, digests, uniqueness, ordering, and aggregate
size before manifest serialization.

`tests/test_snapshot.py` uses temporary fixture files to cover exact round
trips, order-independent identity, modified and missing sources, unknown and
tampered snapshots, unknown paths, path normalization and traversal, duplicate
paths, non-regular and oversized files, file-count and aggregate caps, Windows
case aliases, ADS/trailing-dot-space names, malformed and oversized handles,
reparse-bit recognition, Windows handle-walk reads, the pre-normalization path
limit, and POSIX dirfd usage plus ancestor/final symlink rejection. A
deterministic seam swaps the final POSIX entry for a symlink immediately before
the relative open. Another swaps a root ancestor for a symlink after the
caller path was resolved lexically and immediately before root-chain
acquisition. Both must fail closed without returning source bytes.

## Verification

Command:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider tests/test_snapshot.py
```

Current Windows-host result after the root-chain change: `18 passed, 4
skipped`. The three POSIX-specific tests and OS symlink-creation fixture were
skipped by Windows pytest. On Ubuntu 24.04 WSL (Python 3.12.3), the snapshot
and artifact-store suites ran using cached pytest 8.4.2 and pluggy 1.6.0 from
the approved data root, with no package installation: snapshot **20 passed, 2
skipped** and artifact store **22 passed**. The snapshot skips are Windows
case-alias and native Windows handle-walk tests.
`PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider` were set. A separate
stdlib-only smoke check had already passed exact nested dirfd retrieval,
deterministic final symlink replacement rejection, and root-ancestor symlink
replacement at the root-acquisition seam. The Windows native nested handle-walk
test, deterministic reparse-bit test, and Windows case-alias rejection ran.
Scoped `git diff --check` passed for the three delivered paths.

## Limits and follow-up

The manifest is an in-memory value, not a durable handle registry or a
persistent artifact store. A snapshot hash is content/path identity and does
not identify a particular root directory. On Windows, after the initial
caller-supplied root path is opened, relative traversal uses pinned directory
handles rather than re-resolving child paths; write/delete sharing is denied
for the duration of the read. The initial root path and any reparse points in
its ancestors are resolved before the root handle is acquired, so the caller
must treat the explicitly supplied root path as trusted. Handle-sharing
protection relies on filesystem adherence to Windows sharing semantics.

On POSIX, root and child components are opened from pinned parent descriptors;
no ancestor pathname is re-resolved after walking begins. Replacing a root
ancestor with a symlink before acquisition is rejected, as is replacement of
the final source by a symlink before its open. Relative root inputs rely on
the process current directory when converted to an absolute lexical path.
POSIX does not provide the Windows-style share-deny-write/delete lock here;
in-place concurrent writers may use preexisting descriptors. Metadata and
SHA-256 checks reject detected mutation and never return bytes that fail the
admitted hash. POSIX pytest fixtures have now run in WSL using cached
dependencies, with two Windows-specific skips. Neither implementation provides
power-loss durability. The bounded artifact store and artifact roundtrip are
implemented in separate accepted slices. Root binding/discovery, production
retention and recovery, and request-lifetime pinning remain open E0 work.
Independent review accepted this bounded increment; POSIX pytest follow-up is
recorded in `docs/evals/wrench-e0-snapshot-retrieval/review.md`.
