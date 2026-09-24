# E0 configured-root snapshot binding handoff

Job: `W2-E0-ROOT-BOUND-20260924`

## Change

`src/wrench_harness/snapshot.py` now emits
`wrench.source-snapshot.v2`. Its canonical digest includes the SHA-256 of the
normalized absolute configured root path and the existing sorted source
records. The identity hashes the normalized lexical absolute configured path;
it does not hash the later resolved safe-read path. `create_snapshot` and
`retrieve_exact` convert the caller path once, then use that same `Path` value
for identity and safe reads. Windows normalization follows `normcase`, while
POSIX keeps its case-sensitive path semantics. Retrieval checks the configured
path hash before opening any selected source. It returns `unknown_snapshot` on
a cross-root match attempt and retains the previous exact size/content-hash
verification.

The public function signatures are unchanged. `SourceSnapshot` appends an
optional `root_location_sha256` field for constructor compatibility, but
validation requires a valid digest and v2 schema. Thus old v1 or three-field
manifests fail closed. Snapshots with identical relative files and bytes in
different configured roots have different identities.

## Identity and privacy boundaries

This is configured-path consistency only. It is not physical-directory
identity, owner/session authentication, a trust boundary, or proof of who
created the manifest. Replacing a directory at the same path with identical
files still matches. A root rename changes its identity. The digest does not
include the raw path, but the unsalted SHA-256 can be guessed for likely paths;
keep snapshot values local and do not treat the digest as anonymization.

No OpenCode package was installed or executed. The context hook is not claimed
to veto dispatch. Provider wire projection, tokenizer equivalence, lifecycle
accounting, and matched-task utility remain outside this slice.

## Verification

The following seven focused suites ran on each platform: snapshot, artifact
store, snapshot context, snapshot artifact context, snapshot structural index,
E0 context pipeline, and outcome receipt.

Final Windows Python 3.11.16 run, using cached pytest 8.4.2 and pytest fixtures
under `C:\\wrench-slm-data\\tmp\\w2-e0-root-bound-final-win`:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONPATH='C:\Users\stanc\github\wrench-slm\src;C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider --basetemp='C:\wrench-slm-data\tmp\w2-e0-root-bound-final-win' tests/test_snapshot.py tests/test_artifact_store.py tests/test_snapshot_context.py tests/test_snapshot_artifact_context.py tests/test_snapshot_structure.py tests/test_e0_context_pipeline.py tests/test_outcome_receipt.py
```

Result: **115 passed, 7 skipped**. The skips are the three POSIX-specific
snapshot cases, unavailable Windows symlink fixtures, and Windows artifact
store symlink fixtures.

Ubuntu 24.04 WSL Python 3.12.3 used cached pytest 8.4.2 and pluggy 1.6.0 from
the approved data root, with no package installation and fixtures under
`/mnt/c/wrench-slm-data/tmp/w2-e0-root-bound-final-linux`:

```powershell
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=/mnt/c/Users/stanc/github/wrench-slm/src:/mnt/c/wrench-slm-data/cache/wrench-v2-test-deps-20260923/site-packages python3 -B -m pytest -p no:cacheprovider --basetemp=/mnt/c/wrench-slm-data/tmp/w2-e0-root-bound-final-linux tests/test_snapshot.py tests/test_artifact_store.py tests/test_snapshot_context.py tests/test_snapshot_artifact_context.py tests/test_snapshot_structure.py tests/test_e0_context_pipeline.py tests/test_outcome_receipt.py
```

Result: **120 passed, 2 skipped**. The skips are Windows-only path alias and
native Windows handle-walk tests. Both final runs include cross-root,
normalized-location, old-schema, malformed-location, missing-root, and
single-conversion `PathLike` cases.
`git diff --check` passed. Storage job
`W2-E0-ROOT-BOUND-FINAL-20260924` reserved 50,000,000 bytes; the checker
remained `WITHIN_LIMIT`. Four fixture trees remain under the approved data
root; the final inventory was 1,953 files totaling 20,008,338 bytes, included
in the checker total and below the 50 GB aggregate ceiling.
