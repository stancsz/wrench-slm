# Iteration 216 protocol: explicit required-symbol retrieval

Date: 2026-09-29 (America/Edmonton)
Job: `WRENCH-CODETASK-MVP-ITER216-SYMBOL-DEDUP-20260929-01`
Nonce: `a53f6bc8-0736-48f1-ac79-af11cb5f7955`
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`
Heartbeat goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch noted; no training)

## Question and scope

Iteration 215 proved that the deterministic exact TOML table span works when the configuration path is explicitly required, but the required Python file remained whole-file plus symbol references. Iter216 tests an explicit `symbol:calculate_retry_delay` context query, derived from the function name already present in the unchanged task request, while keeping `src/retry.py` required and `config/service.toml` additionally required with exact table spans. This is an exploratory, development-only optimization on the same previously used synthetic task. The changed query is a deliberate retrieval-policy change and must be reported; the experiment cannot estimate independent success or generalize to unknown symbol requests.

## Frozen pair and identities

- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter216.py`, SHA-256 `20ac81c2eb4efead3b5a4d690b77145cd5797bbdbc7317f2d4b1231e049008f2`.
- Helper: `examples/gateway_context_mvp/run_local_model_mvp.py`, SHA-256 `b54d0a5b76c7dd590b6cbb58e2462a40cd61afe88001ec535c6c0fe892fb960b`.
- Only Wrench's retrieval query changes to the exact symbol named in the task; full-context baseline uses the same five fixture files and identical user/system prompts. Other model, decoding, verifier, retry, context-budget, resource and output settings match Iteration 215.
- The prepared arm requires both `src/retry.py` and `config/service.toml`; table spans are enabled. Verify the TOML reference is an exact parser-reported table and Python reference is an exact parser-reported symbol with function body. Preserve full-file references if the pipeline still selects them; do not claim deduplication otherwise.
- Pinned model: `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base only; no LoRA. Compare actual input IDs, generated output IDs, retries/recovery and deterministic verification. Helper source-local counts are diagnostics, not the outer paired baseline.

## Integrity and resource gates

Output is no-clobber at `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\code-task-iter216-qwen35-4b.json`. A 100,000,000-byte unique reservation was admitted; storage status includes `C:\\wrench-slm-data`, Docker WSL model volume, and this automation directory. Recheck status and C: headroom (>=5 GiB), and require >=10% RAM/VRAM free before and during inference with the in-process sampler and independent pre/post GPU cross-check. Use pinned offline local runtime and Python socket blocking only. Do not call SubRoute/provider, read credentials, mutate a real repository, or access held-out data. Preserve candidate inactive.

This ablation cannot prove any 95/5/95 product gate, Frontier token or dollar savings, LoRA utility, model-size winner, or all-day engineering.
