# Artifact-store oversized-manifest recovery review

Date: 2026-09-25
Goal: [E0 bounded artifact store](../../goal/wrench-e0-artifact-store/GOAL.md)
Job: `W2-NS-STORE-RECOVERY-REVIEW-20260925`
Nonce: `STORE-REVIEW-A6C1`
Baseline and observed HEAD: `d054e4a67024a5c828f114529a458f090964266f`
Status: independent source review **PASS**; supervisor-reported focused tests **PASS**

## Reviewed scope

Reviewed the working-tree diff in `src/wrench_harness/artifact_store.py` and
`tests/test_artifact_store.py` against the E0 artifact-store goal, the North
Star storage and recovery policy, and the earlier recovery-regression report
and evaluation. The reviewed patch is 3,630 bytes with SHA-256
`0b6f8613b121dd94d88b70c0a29df431c12c4864e34e8c9fcadfaba959c245d8`.
At review time, file SHA-256 values were:

- `src/wrench_harness/artifact_store.py`: `f9d589820fefee2f9a2417981a5d0ddffac7cf7b08fb799fb4c9033a9db5080b`
- `tests/test_artifact_store.py`: `954d5c98dd7c14594e0e2f8d931f40370b42142eacd6ef56b4a202a4dc91a540`

The worktree also contains a separate change to `candidate_identity.py`; it was
outside this review. The untracked `uv.lock` was preserved and not reviewed.

## Source review

Finding addressed: an oversized `manifest.json` previously raised from
`_manifest_raw` before `_load_recover` could inspect a valid previous
generation. The new path catches only the explicit manifest-size corruption,
records that slot as unreadable, and continues validating the other slot. A
valid `manifest.prev.json` is still decoded and checked against on-disk object
references before restoration; invalid or absent recovery evidence remains a
corruption result. The added test exercises the oversized-current/valid-previous
case and checks both the restored content and one-entry generation state.

Source review found no remaining correctness defect in this change. A
single-process review cannot establish crash durability, cross-process
coordination, torn-write behavior, or directory metadata persistence.

## Test evidence

Exact focused test case: `test_oversized_current_manifest_recovers_valid_previous_generation`
in `tests/test_artifact_store.py`.

The supervisor reports that its first invocation failed during pytest
temporary-root setup (5 setup errors; no test code ran). After creating this
job's parent directory under the approved cache, the focused manifest-recovery
selection reported **5 passed, 36 deselected in 1.24s** and the complete module
reported **38 passed, 3 skipped in 3.98s**. The skips are existing symlink
privilege cases. Pytest temporary directories remained under
`C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925`.

The first attempted invocation omitted creation of the job's temporary-root
parent and failed during pytest fixture setup (5 setup errors; no test code
ran). After creating the parent, the supervisor ran these exact commands in
PowerShell with existing Python 3.11.16 and cached dependencies:

```powershell
$env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'; $env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -q -p no:cacheprovider tests/test_artifact_store.py -k 'manifest_recovery or oversized_current_manifest or no_valid_manifest or unencodable_or_deep_current_manifest' --basetemp C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925\pytest-tmp
```

Result: **5 passed, 36 deselected in 1.24s**.

```powershell
$env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'; $env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -q -p no:cacheprovider tests/test_artifact_store.py --basetemp C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925\pytest-tmp-full
```

Result: **38 passed, 3 skipped in 3.98s**. The skips are existing symlink
privilege cases. Temporary directories remained under
`C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925`; no package was
installed. The supervisor also reports `git diff --check` passed. These are
supervisor-provided execution results; this reviewer did not run tests. Source
review and test evidence remain distinct.

## Limits and next action

This is a bounded source review plus focused offline regression evidence. It
does not qualify E0 as a whole, nor demonstrate power-loss recovery or
production use.
