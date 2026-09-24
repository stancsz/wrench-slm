# E0 bounded artifact store handoff

Job: `W2-E0-ARTIFACT-STORE-20260924`

Nonce: `ARTSTORE-2c91ef`
Baseline: `36d2d1d89bd4eb3036a3bb2874866fff517d5900`

## API and limits

`src/wrench_harness/artifact_store.py` exposes `ArtifactStore(root)`,
`put(...)`, `read(handle)`, `request()` and `evict(target_bytes=...)`. A caller
must supply a dedicated root and the bytes themselves, along with snapshot
SHA-256, normalized source path, and expected content SHA-256. The store
re-hashes bytes before accepting them. It does not locate sources or validate
that a supplied snapshot/path pair came from a separate snapshot service; it
persists the caller's asserted identity and exact supplied bytes.

Hard limits are 256 KiB per object, 64 content objects, 256 KiB per manifest,
128 manifest entries, 512 eviction tombstones, 8 staging files of at most
256 KiB each, and 8 MiB across manifests, object files, and staging files.
Directory enumeration is capped at max-plus-one before failure. Unknown root,
object, or staging entries, links/reparse points, malformed manifests, and
invalid object hashes fail closed without deleting the entries.

Before store directories are created or used, the implementation walks from
the filesystem anchor through every component of the absolute caller-supplied
root. Each existing component is inspected with `lstat`; links, Windows
reparse points, and non-directory components are rejected. Missing components
are created one at a time after their parent was validated. The regression test
places a symlink in an ancestor and confirms that no store directory is created
at its target.

## Recovery, pins, and eviction

Objects are named by SHA-256. Object bytes are staged under the same store root,
flushed, re-read and verified, then atomically renamed into `objects/`. The
current manifest is wrapped in a content checksum. Before replacing it, the
current verified manifest is staged and atomically installed as
`manifest.prev.json`; the new manifest is then atomically installed as
`manifest.json`.

At open, the store validates object names and bytes plus current and previous
manifest checksums and references. A valid current manifest is used. If current
is invalid or missing and previous is valid, the previous manifest is restored
and `recovery_status` reports that action. If neither is valid, open raises
`ArtifactStoreCorruption` and leaves existing files untouched. Leftover
staging files are retained and reported; they are never promoted. Verified
orphan objects are retained and count toward limits. A partial or hash-mismatched
object causes corruption rather than promotion.

`with store.request() as request:` creates request-local pins. `request.pin()`
verifies the handle and pins it until scope exit. Eviction orders candidates by
insertion generation and handle ID, skips pinned handles, writes a bounded
tombstone, commits the reduced manifest twice, and only then removes recognized
hash-named objects referenced by neither manifest. Reads return `EVICTED` for
retained tombstones, `MISSING` for unknown/expired handles, and `CORRUPT` for
object verification failures.

## Verification

The focused command was run with `TEMP`, `TMP`, and `TMPDIR` set to
`C:\wrench-slm-data\tmp\W2-E0-ARTIFACT-STORE-20260924`, bytecode and pytest
plugin autoload disabled, and the preinstalled Python 3.11 runtime. Result:
`19 passed, 3 skipped`. The three symlink tests were skipped because this Windows
account could not create symlink fixtures. Tests cover exact round trips,
identity binding, object/count/manifest/aggregate/staging caps, rejection before
creating a ninth stage through both manifest writes and object puts, malformed
handles, pin protection, deterministic eviction, tombstones, previous-manifest
restore after deep JSON and escaped-lone-surrogate parse/checksum failures,
fail-closed corruption, interrupted staging retention, and unknown user-file
preservation, and symlinked store-ancestor rejection. The Ubuntu 24.04 WSL
Python 3.12 stdlib smoke passed root-chain symlink rejection, exact read, and
reopen; no packages were installed. Scoped `git diff --check` passed. Storage
status was `WITHIN_LIMIT`; the active 32 MB reservation remains associated
with this job.

## Limits

This primitive is standalone and not connected to source snapshots, context
assembly, clients, or a runtime. Locks and pins exist only in one
`ArtifactStore` instance; callers must use one instance per root and must not
allow multiple processes or external writers to mutate the root. Root-chain
checks do not pin directory handles, so a hostile process concurrently
replacing a validated ancestor between `lstat` and a later path operation could
still redirect that operation. The caller must protect the root chain from
concurrent namespace changes. Atomic rename
and file `fsync` provide bounded same-volume staging, but this slice does not
claim directory-entry fsync, power-loss durability, or recovery across volume
loss. Previous manifests share the same volume. The store has no automatic
retention policy and does not silently evict to make a `put` succeed; callers
must request eviction explicitly.
