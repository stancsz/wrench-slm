# Artifact-store oversized-manifest recovery evaluation

## Decision

**PASS for the reviewed source change and supervisor-reported focused tests.**
The reviewed change allows recovery to inspect a valid previous generation
when the current manifest exceeds its configured byte limit. This does not
complete E0 acceptance.

## Independent review

- Job: `W2-NS-STORE-RECOVERY-REVIEW-20260925`.
- Nonce: `STORE-REVIEW-A6C1`.
- Baseline and observed HEAD: `d054e4a67024a5c828f114529a458f090964266f`.
- Reviewed patch SHA-256: `0b6f8613b121dd94d88b70c0a29df431c12c4864e34e8c9fcadfaba959c245d8`.
- Reviewed files: `src/wrench_harness/artifact_store.py` and
  `tests/test_artifact_store.py` only.
- Result: **PASS**, no source-level findings in the reviewed patch.
- Evidence: source control flow catches the explicit size-limit error per
  manifest slot, then validates the fallback manifest and all referenced
  objects before restoring it. The regression fixture exercises this branch.
- Limit: this is independent source review, not execution evidence or a claim
  of E0 acceptance.

## Verification

- Exact case: `tests/test_artifact_store.py::test_oversized_current_manifest_recovers_valid_previous_generation`.
- Supervisor reports the first command failed during pytest temporary-root
  setup (5 setup errors, no test code). After creating the job parent under the
  approved cache, the focused manifest-recovery selection reported **5 passed,
  36 deselected in 1.24s**; the complete module reported **38 passed, 3 skipped
  in 3.98s**. The skips are existing symlink privilege cases. Temporary
  directories remained under
  `C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925`.
- The first attempted invocation omitted the job-owned temporary-root parent
  and failed in pytest fixture setup (5 setup errors; no test code ran). After
  creating it, the supervisor reports the following successful PowerShell
  commands using the existing Python 3.11.16 and cached dependencies:

  ```powershell
  $env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'; $env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -q -p no:cacheprovider tests/test_artifact_store.py -k 'manifest_recovery or oversized_current_manifest or no_valid_manifest or unencodable_or_deep_current_manifest' --basetemp C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925\pytest-tmp
  ```

  Result: **5 passed, 36 deselected in 1.24s**.

  ```powershell
  $env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'; $env:PYTHONDONTWRITEBYTECODE='1'; & 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -q -p no:cacheprovider tests/test_artifact_store.py --basetemp C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925\pytest-tmp-full
  ```

  Result: **38 passed, 3 skipped in 3.98s**. The skips are existing symlink
  privilege cases. Test temporary directories stayed under
  `C:\wrench-slm-data\cache\W2-NS-STORE-RECOVERY-VERIFY-20260925`. No packages
  were installed. The supervisor also reports `git diff --check` passed.
  Reviewer did not run tests; execution results are supervisor-reported.

## Limits and next action

This review does not establish power-loss durability, cross-process safety,
volume-loss recovery, complete E0 acceptance, or production qualification.
The reported module result includes the named focused case. Retain the initial
infrastructure failure in the evidence history.

See the [source-review report](../../reports/wrench-e0-artifact-store/recovery-hardening.md),
the [E0 artifact-store goal](../../goal/wrench-e0-artifact-store/GOAL.md), and
the [North Star storage and recovery policy](../../northstar/STORAGE_AND_RECOVERY.md).
