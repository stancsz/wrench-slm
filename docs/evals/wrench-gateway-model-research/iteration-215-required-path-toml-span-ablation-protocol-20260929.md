# Iteration 215 protocol: required-path TOML span ablation

Date: 2026-09-29 (America/Edmonton)
Job: `WRENCH-CODETASK-MVP-ITER215-REQUIRED-TOML-20260929-01`
Nonce: `bf338445-9c62-4a4b-88fa-cfcf7a28055a`
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`
Heartbeat-declared goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch preserved; no training)

## Question

When both `src/retry.py` and `config/service.toml` are explicitly required evidence, does Wrench replace the whole TOML file with its exact table span while retaining the Python implementation evidence, and can the unchanged local code task still pass its deterministic verifier? This is a development ablation on the same previously used authored synthetic task, not an independent episode, held-out evaluation, or representative success-rate estimate.

## Frozen comparison

- Runner `examples/gateway_context_mvp/run_code_task_local_mvp_iter215.py`, SHA-256 `97c003fc428d2e874f6f5e09a46d08907627d4769c146ba2ebb46b928fc685e6`.
- Helper `examples/gateway_context_mvp/run_local_model_mvp.py`, SHA-256 `b54d0a5b76c7dd590b6cbb58e2462a40cd61afe88001ec535c6c0fe892fb960b`. It accepts a validated optional tuple of additional required fixture paths; default behavior remains unchanged. Iter215 explicitly adds `config/service.toml` to the required evidence while `src/retry.py` remains the task's required path.
- Context mode `compact_json_segments`; TOML table spans enabled. Full-context baseline still uses all five fixture files. No task/prompt/model/verifier/retry/context-budget/decode setting changes.
- Pinned model `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base only, no LoRA.
- Compare actual model input IDs and generated output IDs per arm. Treat helper-local context target counts as diagnostics only; they are not the outer full-context paired denominator. Audit exact selected source refs, snapshot/content hashes, required quotes, retries, recovery, and deterministic checks.

## Integrity and resource gates

- Output: no-clobber `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\code-task-iter215-qwen35-4b.json`.
- Storage reservation: unique job reservation of 100,000,000 bytes; the storage checker includes the repository, approved root, Docker WSL model volume, and automation directory. Check status before load and after completion, and keep the aggregate below 50 GB. C: must retain at least 5 GiB free.
- Require >=10% free RAM and VRAM before and throughout; use the in-process sampler and independent pre/post GPU cross-check. Exact pinned local environment, offline model loading, and Python socket block only.
- No provider/SubRoute calls, credentials, real repository writes, or held-out access. Keep the LoRA candidate inactive. Abort and record any identity change, output conflict, resource breach, missing provenance, or verifier failure.

A result here cannot prove any 95/5/95 product target, Frontier savings/cost, model-size winner, LoRA utility, or all-day engineering.
