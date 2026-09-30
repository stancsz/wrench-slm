# Iteration 215: required-path TOML span ablation

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER215-REQUIRED-TOML-20260929-01`  
Nonce: `bf338445-9c62-4a4b-88fa-cfcf7a28055a`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`  
Heartbeat-declared goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (still mismatched)

## Result

Both arms completed in one attempt and passed the same AST allowlist and six fixed behavioral cases. This repeats the Iteration 211/213/214 authored synthetic Python retry task, so it is a development ablation, not an independent episode, holdout, or rate estimate.

| Arm | Actual input IDs | Output IDs | Full-lifecycle local tokens | Generation seconds | Verified |
|---|---:|---:|---:|---:|---|
| Full five-path context | 8,805 | 85 | 8,890 | 40.5786 | Yes |
| Wrench, two paths with TOML table required | 467 | 85 | 552 | 32.7608 | Yes |

Actual prompt-input reduction was **94.6962%**. Input-plus-output local-token reduction was **93.7908%**, improving Iteration 213/214 by 0.6412 percentage points, but still below 95%. The Wrench context removed 57 input IDs and 57 full-lifecycle local tokens compared with Iteration 214. To reach 95% against the 8,890-token baseline, Wrench must use no more than 444 total local tokens; at 552 it remains 108 tokens above that threshold.

The exact source receipt now contains `config/service.toml` as `configuration_table`, `parser_reported_exact_table`, lines 7-13, parser `tomllib-table-v1`; the full TOML file is no longer selected. It retains all three required quotes. However, `src/retry.py` still appears as a whole-file `source` reference and as parser-reported symbol spans at 14-16, 7-11, 19-20. This source duplication is the next pruning gap. The selected source content hashes and snapshot identity remain bound in the receipt.

Context helper's two-path source-local comparator reports 419 baseline input IDs, 465 Wrench target IDs, or -10.9785% reduction. That comparator is not the registered five-path full-context baseline. Use the outer actual generation IDs (8,805 versus 467) for the paired comparison. This scope distinction is kept explicit; do not substitute helper estimates.

No retries or recovery fetches occurred. Frontier calls were zero; Frontier tokens/savings, local energy, and all-in cost are null. Local tokenizer reduction is not Frontier savings or billed cost.

## Identity and safeguards

- Protocol `docs/evals/wrench-gateway-model-research/iteration-215-required-path-toml-span-ablation-protocol-20260929.md`, SHA-256 `a0bd2d26b418fe04b927b800ecd13ea435a1a5a5752153c66a4359331fbdc555`.
- Runner `examples/gateway_context_mvp/run_code_task_local_mvp_iter215.py`, SHA-256 `97c003fc428d2e874f6f5e09a46d08907627d4769c146ba2ebb46b928fc685e6`.
- Helper `examples/gateway_context_mvp/run_local_model_mvp.py`, SHA-256 `b54d0a5b76c7dd590b6cbb58e2462a40cd61afe88001ec535c6c0fe892fb960b`. The new optional additional-required-path argument is validated and leaves default behavior unchanged.
- Receipt `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\code-task-iter215-qwen35-4b.json`, 13,049 bytes, SHA-256 `80a6c7af8dfe4e9c8055d089672ceba6639c73eb54e1576b38a1c77ac81a50e1`. Fixture SHA-256 `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`; context snapshot SHA-256 `38b503164cdf1b0ada0aeb685fc1538265bc0552d1772790ec9c9761ddf9e048`.
- Model `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base, no LoRA, 14 files totaling 9,342,907,469 bytes. Runtime 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2; NVIDIA GeForce RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. Load 29.7759s; total 103.7638s. Peak CUDA allocated/reserved 11,590,978,048/11,924,406,272 bytes.
- 187 in-process samples; minimum RAM free 19.5740%, VRAM free 22.5170%; no floor breach or monitor error.
- Python socket connects were blocked, not OS-level network isolation. No provider/SubRoute, credentials, held-out data, real repository writes, or activated adapter.
- Storage reservation was 100,000,000 bytes. The receipt and report were counted before release; C: remained well above 5 GiB free.

## Decision

This confirms the Iter214 issue was declaration wiring and that the TOML table-span path works when the configuration file is explicitly required. The context helper's optional argument is narrowly scoped and default behavior remains the prior contract. To push savings further, examine the unexpected whole-file Python source alongside its exact spans, then remove duplication only when snapshot-bound recovery and all required behavior evidence remain available. The 95/5/95 claims, Frontier savings/cost, LoRA utility, model-size winner, and all-day engineering are not proven.
