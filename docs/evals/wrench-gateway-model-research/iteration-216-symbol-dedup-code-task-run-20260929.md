# Iteration 216: explicit required-symbol retrieval

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER216-SYMBOL-DEDUP-20260929-01`  
Nonce: `a53f6bc8-0736-48f1-ac79-af11cb5f7955`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`  
Heartbeat-declared goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch remains)

## Result

Both arms completed in one attempt and passed all six deterministic behavior checks. The paired result reuses the known Iteration 211/213/214/215 authored synthetic Python retry task, so it is a development diagnostic, not an independent task rate, holdout, or representative coding result.

| Arm | Actual input IDs | Output IDs | Full-lifecycle local tokens | Generation seconds | Verified |
|---|---:|---:|---:|---:|---|
| Full five-path context | 8,805 | 85 | 8,890 | 36.3085 | Yes |
| Wrench, explicit symbol query | 359 | 85 | 444 | 35.9834 | Yes |

Actual prompt-input reduction was **95.9228%**. Input-plus-output local-token reduction was **95.0056%**, crossing the 95% local-token diagnostic by only 0.0056 percentage points (444 vs the 8,890-token full-context baseline). This is the highest full-lifecycle local-token reduction measured in the current paired demo sequence. It is one known synthetic task with an explicit name-targeted retrieval query, not evidence of a general 95% outcome. Local-model tokenizer savings are not Frontier-token savings or billed cost reduction.

The source receipt contains exactly two selected references: `src/retry.py` as parser-reported exact Python symbol lines 14-16, and `config/service.toml` as `whole_file`. All three required code/config quotes were visible, and the model generated the same correct function. Thus the name-targeted path removes the duplicate Python whole file and unrelated symbols, while TOML remains unpruned. Iteration 216 does **not** demonstrate TOML span use: source inspection shows table-candidate construction is bypassed when the query is symbol-targeted. The helper reports 419 source-local baseline IDs versus 357 prepared IDs (14.7971%); use the actual outer generation counts for comparison because its baseline is two-source-only, unlike the full five-path baseline.

No retries or recovery fetches occurred. Frontier calls were zero; Frontier tokens, provider savings, local energy, and all-in cost are null.

## Identity and safeguards

- Protocol `docs/evals/wrench-gateway-model-research/iteration-216-symbol-dedup-code-task-protocol-20260929.md`, SHA-256 `8c8815dec6036fb902a8cea9411bb142fa41d9f71b9b4f7bfeb7b02f99acb20f`.
- Runner `examples/gateway_context_mvp/run_code_task_local_mvp_iter216.py`, SHA-256 `20ac81c2eb4efead3b5a4d690b77145cd5797bbdbc7317f2d4b1231e049008f2`.
- Context helper `examples/gateway_context_mvp/run_local_model_mvp.py`, SHA-256 `b54d0a5b76c7dd590b6cbb58e2462a40cd61afe88001ec535c6c0fe892fb960b`.
- Receipt `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\code-task-iter216-qwen35-4b.json`, 10,879 bytes, SHA-256 `c7bbf284761890716a7d5f5e05e2b234e3ff3d21415acc104b475dc7be2192e3`. Fixture SHA-256 `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`; context snapshot SHA-256 `f44dfb961e03c5a33aba23c567ef65a714d07fd2d54846c0fb1440cbc1e812cb`.
- Model `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base, no adapter, 14 files totaling 9,342,907,469 bytes. Runtime 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2; NVIDIA GeForce RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. Load 28.1216s; total 100.9780s. Peak CUDA allocated/reserved 11,596,884,480/12,060,721,152 bytes.
- 181 samples; minimum free RAM 19.5178%, VRAM 21.7649%; no reserve breach or telemetry error.
- Python socket connects blocked; not OS-level isolation. No provider/SubRoute, credentials, real-repository writes, held-out data, or LoRA activation.
- The 100,000,000-byte storage reservation remained in scope through report creation and was released after counting the receipt/report. The final checker remained `WITHIN_LIMIT`; C: free space exceeded 5 GiB.

## Decision

The explicit function symbol is an efficient deterministic retrieval handle for this exact request: one correct function span plus the config file passes the fixed verifier using 444 total local tokens. This is narrow mechanical-evidence success only. A next experiment may preserve explicit symbol targeting while enabling the independently required TOML table span, then measure whether it lowers tokens further without losing the configured value or changing the generated result. No 95/5/95 Frontier claim, all-in-cost claim, LoRA benefit, best-model decision, or all-day engineering requirement is established.
