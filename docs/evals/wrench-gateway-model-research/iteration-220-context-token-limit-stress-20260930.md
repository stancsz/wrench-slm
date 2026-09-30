# Iteration 220: realistic-context token screen hits E0 admission limit

Date: 2026-09-30 (America/Edmonton)  
Job ID: `WRENCH-CODETASK-ITER220-NOISE-FIXTURE-20260930-01`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Heartbeat-declared gateway goal SHA-256: `b847d638b0ca4f9c24041dccec2fb440861f0b27be0441e37e288057f701b027`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59` (mismatch)

## Question

Iteration 219's 12 tiny synthetic tasks prepared successfully, but Wrench framing increased prompt input from 3,461 to 4,027 token IDs. This screen asks whether query-only context selection can reduce tokens when each synthetic repository also contains realistic adjacent-service notes, tests and telemetry logs.

## Frozen fixture and method

Iteration 220 preserves all 12 Iteration 219 tasks, source files and oracles byte-for-byte. Each of three synthetic repositories adds operational notes, unrelated telemetry code/tests and 600 adjacent-service log rows divided into four time-sliced files. The extra text contains no oracle quote. This is authored synthetic material, not a representative production repository sample. The manifest validates under the existing 12-task / four-family contract.

The measurement used the exact local Qwen3.5-4B tokenizer from revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, offline. It did not load model weights or run inference. Retrieval received only the task query; oracle paths were not passed into E0. Every preparation failure received the full-context fallback and remained in the denominator, with zero savings credit.

## Result

All **12/12** E0 preparations failed with `context_failed: ContextAdmissionError`, captured as `logical_context_limit_exceeded`. The paired measurement therefore used full-context fallback for all episodes:

| Measure | Result |
| --- | ---: |
| Full-context input IDs | 369,817 |
| Wrench-prepared input IDs after zero-saving fallback | 369,817 |
| Credited input reduction | 0% |
| E0 preparation failures | 12 / 12 |
| Oracle quotes present in the full-context fallback | 20 / 20 |
| Model weights loaded / inference | No / No |
| Frontier or SubRoute calls | 0 |

This is a **deterministic runtime admission failure**, not evidence that retrieval would select the wrong segments or that model quality failed. It identifies a concrete ceiling: E0 admits sources into a logical context limited to 8,192 tokens, while these full-context prompts total about 30,800 tokens per episode. The runtime rejects the source set before it can select the 2,048-token working context. The safe fallback preserves evidence but eliminates token savings.

The 600-line fixture is intentionally a stress case and does not estimate a population success rate. Its results cannot support Frontier-token, cost, coding-success, or all-day reliability claims. The 8,192-token logical admission ceiling is a product-level obstacle to measuring larger-repository savings and should be addressed with a separately bounded source-ingestion limit and tests before another large-context pilot.

## Artifacts and verification

- Iteration 220 manifest: `examples/gateway_context_mvp/iteration220_noise_pilot_manifest.json`, SHA-256 `f80b48ce3269154f45735323d2f97cc8d2110de5b20800f286980f310046d9f4`.
- Deterministic builder: `examples/gateway_context_mvp/build_iteration220_noise_manifest.py`, SHA-256 `0d9a3f049d9167543266372d8dcf3f7b89d00c0b943c2b677588516607c9d46b`.
- Tokenizer-only measurement: `examples/gateway_context_mvp/measure_iteration220_context_only.py`, SHA-256 `82c58ccb279b100886ec2ec43ea6f18a01ebff3c4a11185f2404ac1f9720081c`.
- Machine-readable receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\iteration-220-context-only-token-screen.json`, SHA-256 `4a564c969424802d9f459748799011e0e6336a967652224fdbf50b7743a7f67f`.
- Fixture regression: `tests/test_iteration220_noise_fixture.py`.
- Focused validation: **13 passed** across the Iteration 220 fixture, Iteration 219 contracts and runner preflight tests.

The runner preflight remains fail-closed because the on-disk active-goal hash differs from the heartbeat identity. No local-model run is authorized by this receipt. The held-out split remains unopened; no training, provider use, credential access, or adapter activation occurred.

## Next bounded decision

Add a separately configurable, hard-capped source-ingestion token limit that remains larger than the selected working-context budget, while preserving the existing 8,192-token default and all source-byte/path limits. Test that a >8,192-token source set can be ingested, query-selected into the existing 2,048-token budget, and still fails closed beyond the new cap. Re-run this frozen fixture only after that deterministic change passes focused tests and the active-goal identity is reconciled.
