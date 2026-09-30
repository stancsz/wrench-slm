# Iteration 214: related-path TOML span ablation

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER214-TOML-SPAN-20260929-01`  
Nonce: `7767a481-2ad2-45d6-a810-1e65c004b55e`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`  
Heartbeat goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch remains unresolved)

## Result

The paired run completed. Both arms passed the same AST allowlist and all six fixed behavior checks with one attempt each. This is the Iteration 211/213 previously evaluated synthetic Python retry-function task, not an independent episode or held-out result.

| Arm | Actual input IDs | Output IDs | Full-lifecycle local tokens | Generation seconds | Verified |
|---|---:|---:|---:|---:|---|
| Full five-path context | 8,805 | 85 | 8,890 | 41.2545 | Yes |
| Wrench, two related paths | 524 | 85 | 609 | 32.4193 | Yes |

Observed prompt-input reduction was 94.0488%; observed input-plus-output local-token reduction was 93.1496%. This exactly matches Iteration 213's token counts and remains below 95%. The successful pair is 1/1 on this reused task, not an estimated rate. No retries or recovery fetches occurred. Frontier calls were zero; Frontier tokens, provider savings, local energy, and all-in cost are null. Local tokenizer reduction is not Frontier billing reduction.

## Why the TOML switch did not change context

The option was set to `use_toml_table_spans=True`, but the selected-source receipt still contains the complete `config/service.toml` as `segment_kind=source`, `span_status=whole_file`. It also contains the complete `src/retry.py` plus three exact parser-reported symbol spans. The table-span switch did not replace the full TOML source, so token use and task output matched Iteration 213.

Source inspection explains this: `e0_context_pipeline.py` builds TOML candidates by iterating `required_source_paths`; the public option is specifically `use_toml_table_spans_for_required_path`. Iter214 supplied `config/service.toml` as a related `source_path`, but the task declared only `src/retry.py` as required. Therefore the requested TOML path never entered the table-span candidate path. The next controlled experiment must explicitly exercise both required evidence paths through the helper contract (or first make and review a narrowly scoped interface change); simply flipping this boolean is not an effective ablation.

The context helper separately reports `baseline_target_input_tokens=419` and `target_input_reduction_percent=-24.582339`. That helper baseline is restricted to its two source paths, not the outer full-five-path baseline (8,805 actual input IDs). It is diagnostic only; the table above uses actual input IDs passed to generation for both arms. Do not compare the helper value with the outer baseline.

## Identity and safeguards

- Protocol: `docs/evals/wrench-gateway-model-research/iteration-214-related-path-toml-span-ablation-protocol-20260929.md`, SHA-256 `7267e9860838a7f749db6da8ffa4ec09b5e94cbab08711bfcdddbf44d0d657c2`.
- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter214.py`, SHA-256 `4a7ac25385a72565c4ef97f5a9fc990005b6d7776ffbfbd6a8806d461db671be`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\code-task-iter214-qwen35-4b.json`, 13,003 bytes, SHA-256 `032e74e5cf5c57d5b722109a8657cd1e32c757130e5376f962cb1349f3502e2b`.
- Fixture SHA-256: `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`; context snapshot SHA-256: `58ad05bb3b6e845a7e8911614db9e7c3a0b7eee5a71b87bb45a691669ad80cff`.
- Model: `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base, no adapter; exact inventory has 14 files totaling 9,342,907,469 bytes.
- Runtime: 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2; NVIDIA GeForce RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. Model load 27.9566s; total 102.1906s. Peak CUDA allocated/reserved 11,590,978,048/11,897,143,296 bytes.
- 185 in-process resource samples; minimum free RAM 20.0583%, minimum free VRAM 22.6333%; no floor breach or sampler error.
- Provider-free/local-only run; Python socket blocking is not OS-level isolation. No credentials, SubRoute, held-out data, LoRA, or real-repository mutation.
- Storage reservation was 100,000,000 bytes. The receipt and report were counted before release; C: had 124,738,613,248 bytes free at report time.

## Decision

This negative ablation identifies a wiring mismatch, not a limitation of table-span extraction quality: the API only constructs spans for declared required paths, and this runner declared only the Python file required. Do not claim a TOML span reduction from Iter214. Fix the isolated test's required-evidence declaration before spending another model run, then compare exact selected references and actual paired generation IDs. No product-level completion, Frontier-token, all-in-cost, size-winner, LoRA, or all-day engineering target is established.
