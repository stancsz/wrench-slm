# Phase 280: Luna decoder diagnosis and 64K reference control

Date: 2026-09-21

## Advisor receipt

The concrete blocker was whether the malformed proposal output came from the
4M context path, NVFP4 runtime, chat template, or insufficient model training.
The local investigation already had a repeatable 4M failure and a 64K NVFP4
failure, so a focused Sol consultation was appropriate.

- advisor: `codex-sol-advisor`
- packet characters: 1,596
- prompt tokens: 536
- completion tokens: 283
- total provider tokens: 819
- `decision_changed`: `true`

The advisor verdict was to prioritize decoder/template diagnosis before another
LoRA attempt, using a 64K current-versus-reference control and stopping if a
known-good reference path still failed exact schema or violated the 10% reserve.

## Discriminating experiment

The current NVFP4 package had already produced this 64K result:

- raw tokens: 61,434
- staged tokens: 1,991
- gate latency: 3.488 ms
- total latency: 1,024.030 ms
- model calls: 1
- output: `{"n}{"n}`
- status: `REAL_WORKER_HTTP_4M_GAP`

The BF16 reference checkpoint
`Wrench-Qwen3.6-8expert-profiled-BF16-calibrated-v7-safety` was then run
through the Transformers path with the same 64K compacted payload and proposal
prompt:

- raw tokens: 61,420
- staged tokens: 1,987
- gate latency: 5.078 ms
- total latency: 28,443.508 ms
- model calls: 2, including one bounded repair attempt
- backend: `transformers`, device `cuda:0`
- fallback: `model_output_invalid_json`
- exact proposal: false
- status: `REAL_WORKER_GENERATION_GAP`

Receipt:

- `C:\Users\stanc\AppData\Local\Temp\wrench-bf16-reference-64k-20260921-131f119dcc9d4271991f97ba4312fee4.json`
- SHA-256: `985CFCE584706C11ACB9B569B22B55DBAFAF80B5CA84A909209F9871F9581335`

The two controls fail at the same 64K compacted prompt despite using different
decoder backends. This exonerates 4M context length as the sole cause and makes
a pure NVFP4 replacement insufficient as the next move.

## Constraint finding

The installed FreeToken OpenAI server explicitly rejects
`response_format` types `json_object` and `json_schema` because it has no
constrained or guided decoding. Therefore a grammar-constrained 2x2 cell is
not available on the current native runtime without adding a new decoder
backend.

## Decision

The deterministic embedded toolbelt remains the production-value lane. The
native learned decoder remains diagnostic-only and fail-closed. The next model
experiment, if pursued, must be schema-focused SFT or a decoder/backend with
real constrained decoding, and it must beat the BF16 64K control on exact
proposal validity before any further 4M quality claim is made.
