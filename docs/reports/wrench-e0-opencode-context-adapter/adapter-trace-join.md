# OpenCode prepared-context lifecycle trace join

## Scope

Added two focused integration tests in `tests/test_e0_lifecycle_accounting.py`. The happy path sends a synthetic, one-message OpenCode context-hook event through `materialize_opencode_prepared_context`, projects both the before and adapter-returned after events, and passes those projections plus the adapter-produced inserted message to `build_partial_lifecycle_trace` with the same READY preparation join and finalized fixture outcome. It asserts the READY envelope transition binds the preparation, session, inserted-message digest, gate position, and both projection digests to the adapter transition receipt.

The rejection case supplies the same synthetic event under another session ID. The adapter rejects admission and a lifecycle trace built from that mismatched projection is not READY.

The test path does not inspect or parse `PreparationResult.prompt`. It does not change production code, client configuration, plugins, gateway state, or provider routing.

## Verification

- Base and verified starting HEAD: `b74414e0cb542fa4d37637c9692591432e4f2869`.
- Exact successful invocation (PowerShell):

  ```powershell
  $env:PYTHONPATH='C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages'
  $env:PYTHONDONTWRITEBYTECODE='1'
  .\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider tests/test_e0_lifecycle_accounting.py --basetemp C:\wrench-slm-data\tmp\W2-NS-E0-ADAPTER-TRACE-JOIN-20260925
  ```

- Result: **26 passed in 5.48s** on Python 3.11.16 with pytest 8.4.2. The existing local Python environment did not contain pytest; the run used the already-present bounded test dependency cache and did not install or sync packages.
- `git diff --check`: passed.
- Test source SHA-256: `46a577da1559fac7bdb5613694dbfaa3fdebb07c1cbe670949c4d4948ccd50c0`.
- Storage admission: `WITHIN_LIMIT`, with 10,000,000 bytes reserved as `W2-NS-E0-ADAPTER-TRACE-JOIN-20260925-IMPL`. C: had 182,555,639,808 bytes free. System RAM had 14,117,269,504 of 34,290,302,976 bytes free (~41%). No GPU report was available from `nvidia-smi`; no GPU workload ran. Pytest scratch (30,276 bytes, 143 files) is under the approved `C:\wrench-slm-data\tmp\W2-NS-E0-ADAPTER-TRACE-JOIN-20260925` path.
- Final storage checker status after accounting for the report and test scratch: `WITHIN_LIMIT`. The 10,000,000-byte reservation `W2-NS-E0-ADAPTER-TRACE-JOIN-20260925-IMPL` was released, and the final checker listed only unrelated active reservations.






