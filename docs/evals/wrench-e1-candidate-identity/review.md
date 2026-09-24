# E1 local candidate identity verifier evaluation

Job: `W2-NS-E1-LOCAL-IDENTITY-VERIFIER-20260924`

Nonce: `E1VER-28AD`

Implementation baseline: `405f72e36fa53648e02ac5146dd952cb30eb0464`

## Decision

Accept the bounded offline identity-verification mechanics slice. It checks a
flat local file tree against pinned metadata with exact file-set, size and
digest checks, streaming reads, and a compact receipt. It does not establish
that the real model is present or valid, that a backend can load it, or that
any E1 quality or adapter-composition gate passes.

## Scope and verification

- Implementation: `src/wrench_harness/candidate_identity.py`.
- Synthetic tests: `tests/test_candidate_identity.py`.
- Handoff: `docs/reports/wrench-e1-candidate-identity/identity-verifier.md`.
- Windows Python 3.13.15 focused run: **9 passed, 10 skipped**. POSIX
  traversal cases skip because the implementation fails closed on Windows.
- Ubuntu 24.04 /mnt/c Python 3.12.3 focused run: **18 passed, 1 skipped**.
  Only symlink creation was unavailable on that mounted filesystem.
- Both commands used cached pytest 8.4.2, disabled bytecode and pytest cache,
  and placed temporary fixtures under `C:\wrench-slm-data\tmp`.
- `git diff --check` passed.

Review6 (`W2-NS-E1-LOCAL-IDENTITY-REVIEW6-20260924`, nonce `E1REV6-CC64`)
returned NEEDS_CHANGES because the file path was not rechecked after hashing.
The verifier added a no-follow stat relative to the pinned root after the
stream, comparing type, size, mtime, ctime, device and inode with the original
entry. A deterministic replacement test covers that race window. Fresh
read-only review7 (`W2-NS-E1-LOCAL-IDENTITY-REVIEW7-20260924`, nonce
`E1REV7-A1F3`) returned **PASS** and checked root-component identity, root
pinning, enumeration identity, file reopen and streaming stability, the
post-hash path check, Windows fail-closed behavior, nested-path rejection, and
metadata bounds before serialization. It did not run tests or access model
files.

At the last checker snapshot before final report/eval updates, status was
`WITHIN_LIMIT`: 847,264,010 actual bytes, 15,103,000 active reservations and
862,367,010 projected bytes. This job reserved 15,000,000 bytes and included
the Python 3.13 runtime. Synthetic temporary files and dependency cache were
under the approved data root. Final storage status and reservation release
are reported in the task handoff.

## Authority and limitations

Only tiny synthetic fixture files were hashed. The pinned metadata document
`docs/northstar/model-candidate.json` describes a 1,769,980,465-byte Qwen
snapshot but its files were not opened, hashed, downloaded, or otherwise
accessed. No client, provider, network, training, inference, benchmark, or
packaging operation occurred. The active contract prohibits model weight
downloads, training and inference; this increment grants no new authority.

The receipt attests only that local bytes matched the supplied identities at
verification time. Use a locally controlled snapshot directory because a
filesystem owner can mutate files after verification returns. The helper does
not authenticate metadata provenance, validate model configuration or license
rights, prove recoverability, qualify a runtime, demonstrate adapter
compatibility, or show utility. E1 remains gated on separately approved model
job admission, actual local byte verification, composition validation, and
held-out evaluation.
