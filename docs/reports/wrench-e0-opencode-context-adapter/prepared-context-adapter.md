# OpenCode prepared-context materialization seam

Job ID: `W2-NS-E0-OPENCODE-PREPARED-ADAPTER-20260925-IMPL`  
Nonce: `PREP-7A62-IMPL`

## Result

Added a provider-free adapter for a pinned OpenCode `2.0.15` `session.context`
event. It accepts an `OpenCodePreparationJoin`, checks the existing local
session/admission predicate, and inserts exactly once the context message
retained by the prompt compiler. The message travels through the prompt and E0
results as bounded canonical JSON, excluded from result repr and receipt
payloads. The adapter checks its SHA-256 against the READY prompt-gate receipt,
rejects an existing duplicate, inserts at the bound position, and returns a
materialized copy without changing the input event.

Before returning READY, the adapter projects both event snapshots and requires
`validate_opencode_preparation_context_transition` and
`verify_opencode_prepared_transition_receipt` to succeed. The returned receipt
contains session/version identities, insertion position, and hashes only. The
failure status and reason do not contain context text. The materialized event
necessarily contains the inserted message while held in the caller's memory.

The bridge is compiler output, not reconstructed from `PreparationResult.prompt`.
This is a local structural seam. It does not register an OpenCode plugin,
authenticate a runtime callback, veto dispatch, or establish final provider
serialization/tokenizer parity.

## Verification

Focused synthetic tests: **7 passed** in 0.62 seconds. Runtime was the existing
cached Python `3.11.16` environment with pytest `8.3.5`; no packages were
installed and no provider/client requests were made.

After the public result dataclasses changed, focused regression across
`tests/test_prompt_compiler.py`, `tests/test_e0_context_pipeline.py`,
`tests/test_opencode_hook_projection.py`, and this adapter module passed:
**112 passed** in 4.64 seconds. It used the existing
`W2-NS-E0-OPENCODE-PREPARED-ADAPTER-20260925-REGRESSION` 25,000,000-byte
reservation, which was released after final accounting.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src'
$p='C:\wrench-slm-data\cache\w2-rootbind-uv\archive-v0\j_0R9gSEmCfY82Cp\Scripts\python.exe'
& $p -B -m pytest -p no:cacheprovider --basetemp 'C:\wrench-slm-data\tmp\W2-NS-E0-OPENCODE-PREPARED-ADAPTER-20260925\pytest-basetemp' tests/test_opencode_prepared_context.py
```

The tests cover compiler hash/position binding, one insertion, six preserved
hook fields, message order, input immutability, duplicate rejection, local
readiness and session checks, gate/hash/message mismatches, malformed shapes,
position and message-count bounds, and content-free transition evidence.

The first focused run exposed that the result repr included its materialized
event. The event field is now omitted from repr; the passing test checks that
the result and transition receipt repr do not expose context text.

Storage ended `WITHIN_LIMIT`: 1,710,630,437 bytes actual against the 50 GB
limit, with 103,000 bytes of other workers' reservations. This worker's
25,000,000-byte reservation was released after final accounting. Test scratch
was under `C:\wrench-slm-data\tmp\W2-NS-E0-OPENCODE-PREPARED-ADAPTER-20260925`
and is absent after pytest cleanup. No model, dataset, or other large artifact
was created.

The implementation was prepared on branch `development` at base commit
`d705e11e336f8909ee626976fe9e406377996443`; this worker did not commit. SHA-256
identities at freeze:

| File | SHA-256 |
| --- | --- |
| `src/wrench_harness/prompt_compiler.py` | `4a2d2e206a62122384af46deb37d711e19ffd39009250f42029f698b03a7a359` |
| `src/wrench_harness/e0_context_pipeline.py` | `0646c7b2ab2a2575e75e9eb5a94dde1146498d1f6b0da911fd4783f7f7a5e549` |
| `src/wrench_harness/opencode_prepared_context.py` | `53934d40535ca823873b7be2788d361172b2c16fda017df5f7b8a04d58c95ff9` |
| `tests/test_opencode_prepared_context.py` | `194db28bc8e9b73deb29a5c1794850d820b032cd65e7ec0b0532666c498062c1` |
