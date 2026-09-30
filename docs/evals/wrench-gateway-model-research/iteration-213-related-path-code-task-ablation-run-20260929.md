# Iteration 213: related-path code-task ablation

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER213-RELATED-PATH-20260929-01`  
Nonce: `e4be2407-99d7-42fb-a77e-185cd201ccbe`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Identity and change

- Protocol: `docs/evals/wrench-gateway-model-research/iteration-213-related-path-code-task-ablation-protocol-20260929.md`, SHA-256 `5EA95F3D846C63F24957F88866F3C00C40825C47B20DCB9887CF111E5ECFA951`.
- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter213.py`, SHA-256 `C215AE366FA7B55D6BAA428FB05BFF04F328F5BE74A12511A2C9E648D6DD9639`.
- Runner is an isolated Iteration 211 copy; only its job/nonce/output/schema identities and the Wrench `source_paths` argument changed. Wrench preparation received `config/service.toml` and `src/retry.py`. The full-context baseline still received all five fixture paths. Task, prompts, model, decode limit, verifier, retries and recovery policy stayed fixed.
- Receipt: `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\code-task-iter213-qwen35-4b.json`, 13,006 bytes, SHA-256 `195BD7EA91997744B66F41A4E2C509DBB37882B27DE7408EEBEA6526241060DF`.
- Synthetic fixture SHA-256: `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`; run snapshot SHA-256: `92f66cc657a5c5bba417f4e4697261209e8ba0446534db76d43fd0ff13b16e7e`.

## Paired outcome

This is the same previously evaluated synthetic Python retry-function repair as Iteration 211, not a new independent task. Both arms passed the AST allowlist and all six fixed behavior checks. Each arm used one attempt; there were no retries or recovery fetches. Required source evidence was visible in all three expected quotes.

| Arm | Wrench input paths | Actual input IDs | Output IDs | Full-lifecycle local tokens | Generation seconds | Verified |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Full-context baseline | All five fixture paths | 8,805 | 85 | 8,890 | 40.9449 | Yes |
| Wrench prepared | `config/service.toml`, `src/retry.py` | 524 | 85 | 609 | 32.4897 | Yes |

Using actual IDs sent to generation, prompt-input reduction was **94.0488%** and input-plus-output local-token reduction was **93.1496%**. Relative to Iteration 211's all-five-path prepared arm (596 input / 676 total tokens), this ablation removed 72 input IDs and 67 total IDs while preserving the single task's verified result. Full-lifecycle reduction improved by about 0.754 percentage points, but remained below 95%.

The context-builder's separate target-count fields report baseline 419, prepared 522, and -24.582339% reduction. The helper was invoked with the reduced two-path source scope; that baseline is not the registered full-five-path outer prompt and is not comparable to the actual full-context input count of 8,805. Keep these helper values as a diagnostic and use actual generation IDs for the paired local-model comparison. This reveals an accounting-scope mismatch to correct before the next evaluation; do not silently replace either denominator.

Success retention is `1/1` for this one pair, not a rate estimate. The run made zero Frontier calls. Frontier-token savings, all-in cost, and energy are `null`. Local token reduction is not Frontier usage or provider savings, and no 95% product claim passes.

## Runtime and safeguards

- Model: pinned `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base only; 14 files totaling 9,342,907,469 bytes. No LoRA was loaded or activated.
- Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2; NVIDIA RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.
- Load time: 28.8033 seconds; total: 103.0741 seconds. Peak CUDA allocated/reserved: 11,590,978,048 / 11,897,143,296 bytes.
- Across 184 in-process samples, minimum free RAM was 19.5151%, and minimum free VRAM was 22.6956%. No floor breach or sampler error was reported. Independent pre/post `nvidia-smi` differences from in-process VRAM samples were 1.4695 and 1.3355 percentage points, within the 10-point tolerance.
- Offline/local-only model loading and Python socket blocking were enabled; this is not OS-level network isolation. No held-out data, real repository mutation, credentials, provider, or SubRoute was used.
- Storage reservation: 100,000,000 bytes under this job ID. Storage remained within the 50 GB ceiling during the run. The job process has exited and the receipt/report are counted; release its reservation now. C: had over 125 GB free at admission.

## Decision

Related-path scope preserved this one task and improved actual local prompt reduction, but did not reach 95% on input-plus-output local tokens. This known-task result is exploratory because the task was reused to choose the source-path ablation. It is not confirmatory or representative coding evidence. The next useful pruning diagnostic should remove duplicated whole-file and symbol content only where exact source lineage and all required behavior evidence remain intact, and should bind one common tokenizer-counting scope to both arms. Keep prior Iteration 211 and this receipt immutable.

The heartbeat-declared goal hash `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` still differs from the on-disk goal hash used by this run. Reconcile before any goal-bound package review or training. Provider calls remain closed; the 95/5/95, all-in-cost, model-size winner, and all-day engineering requirements remain open.
