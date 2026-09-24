# E1 local candidate identity verifier

Job: `W2-NS-E1-LOCAL-IDENTITY-VERIFIER-20260924`

Nonce: `E1VER-28AD`

Baseline: `405f72e36fa53648e02ac5146dd952cb30eb0464`

## Scope

Added `src/wrench_harness/candidate_identity.py`, a read-only verifier for the
pinned `wrench.model-candidate-metadata.v1` shape. It bounds the parsed JSON
tree before canonical serialization, validates revision, file sizes and
hashes, rejects unsafe/duplicate paths, and requires exact local file-set
identity. Files are streamed in 64 KiB blocks; the receipt is compact and
bounded. It does not import a model runtime or hold checkpoint contents in
memory.

The supported filesystem slice is deliberately narrow. The manifest must be
flat. On POSIX, the verifier pins a filesystem anchor, opens every path
component relative to its pinned parent with `O_DIRECTORY|O_NOFOLLOW`, and
compares each open handle with the path's observed device/inode. It compares
the final root handle with the initially observed root and checks its open
path before and after enumeration. For each direct child it compares the
enumerator inode with a no-follow stat relative to the pinned root; before
hashing it reopens relative to that root with `O_NOFOLLOW` and compares the
open file identity to the saved entry identity. It verifies identity and
metadata stability after streaming. Platforms that cannot provide these
handle-relative primitives fail closed. Windows currently returns
`handle_relative_no_follow_unavailable` before scanning any path.

## Verification

The focused synthetic tests passed on both available runtimes:

- Windows Python 3.13.15, offline cached pytest 8.4.2:
  `9 passed, 10 skipped`. POSIX traversal tests are skipped because Windows
  fails closed by design.
- Ubuntu 24.04 /mnt/c Python 3.12.3, same offline cached pytest:
  `18 passed, 1 skipped`. Symlink creation was unavailable on the mounted
  filesystem; all other synthetic traversal, root identity, child inode,
  bounded metadata, and digest checks ran.

These later runs collected 19 items and supersede the earlier 18-item run
counts. The captured pytest stdout is in the task transcript; no separate
run receipt or source-tree hash was saved. Tests ran with `HEAD` at
`5f5806a5583883310122b42ebfa50ac68dbc697a` and the verifier/test files in the
working tree. That implementation was later committed as
`5310bb502aec24fd6adf22b0add8d7a9feda1812`; the captured output does not
independently bind the run to a content hash.

Commands used `PYTHONDONTWRITEBYTECODE=1`, disabled pytest's cache provider,
and placed `--basetemp` under `C:\wrench-slm-data\tmp`. The Windows command
used the cached dependency root
`C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages`.
`git diff --check` passed. Independent review6 (`E1REV6-CC64`) found one
remaining race: the path could be replaced after its descriptor was opened
and hashed. The verifier now performs a post-hash no-follow stat relative to
the pinned root and compares type, size, mtime, ctime, device and inode with
the saved enumeration identity. A deterministic synthetic replacement test
covers that interval. Fresh independent review7 (`E1REV7-A1F3`) returned
**PASS** after inspecting the repair and the full requested race-check scope;
the reviewer did not run tests or access candidate files.

The current checker status after the POSIX test run was `WITHIN_LIMIT`: actual
847,264,010 bytes, active reservations 15,103,000 bytes, projected
862,367,010 bytes. This job reserved 15,000,000 bytes and included the Python
3.13 runtime. The test dependency cache and scratch files are under the
approved data root. RAM at the last check was 14,158,248 KiB free of
33,486,624 KiB (about 42%). These focused CPU tests do not use VRAM. The
checker is a storage admission estimate, not an OS quota; final post-release
status is recorded in the handoff.

## Candidate and authority limits

The pinned metadata document is `docs/northstar/model-candidate.json`. It
describes `Qwen/Qwen3.5-0.8B`, revision
`2fc06364715b967f1860aea9cf38778875588b17`, 13 flat entries, and a published
repository byte sum of 1,769,980,465. All 13 entries are flat and have a Git
blob ID; two also have upstream SHA-256 values. The metadata itself states that the
sizes are not local downloaded-byte or hash verification. This task did not
open, hash, download, or otherwise access candidate model files. Only tiny
synthetic fixture files were hashed.

No client, model, provider, network, training, inference, benchmark, or
packaging operation occurred. The receipt is a point-in-time file identity
check; callers should use a locally controlled snapshot directory because a
filesystem owner can mutate files after verification returns. The active contract prohibits unauthorized
weight downloads, training and inference; this verifier does not grant that
authority. A future approved run could attest only that local bytes match
the supplied metadata identities. It cannot authenticate metadata provenance,
validate model format, qualify a runtime, establish adapter compatibility, or
show utility or E1 acceptance.
