# Iteration 214 protocol: related-path TOML table-span ablation

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER214-TOML-SPAN-20260929-01`  
Nonce: `7767a481-2ad2-45d6-a810-1e65c004b55e`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`  
Heartbeat-declared goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch preserved; no goal edit or training)

## Question

Does enabling the existing deterministic TOML table-span extraction for the related `config/service.toml`, while retaining required code-symbol evidence from `src/retry.py`, reduce the Iteration 213 prepared prompt and preserve the exact same synthetic code task's verifier result? This is a reuse of the Iteration 211/213 authored synthetic task, selected after inspecting those outputs. It is a development ablation, not independent or representative evidence.

## Frozen pair

- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter214.py`, SHA-256: `4a7ac25385a72565c4ef97f5a9fc990005b6d7776ffbfbd6a8806d461db671be`. It is an isolated Iteration 213 copy changing job/nonce/output identity and setting `use_toml_table_spans=True`.
- Only the Wrench-prepared arm changes its span option. The full-context baseline still contains all five synthetic fixture paths. Paths, task wording, model, tokenizer, prompts, decode settings, verifier, retries/recovery, resource sampler, output rules, and offline configuration remain as in Iteration 213.
- Model: pinned `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base only; no LoRA.
- Compare actual input token IDs sent to generation and generated output IDs. Count retries/recovery. Context helper baseline fields are limited to the supplied two-path source scope and are not a valid cross-arm denominator; label them diagnostic only. The outer generation-arm counts are the paired comparison.
- Inspect selected source references and required quotes; the table span must retain the configured `max_backoff_ms` value and source lineage.

## Integrity and gates

Output is no-clobber under `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\code-task-iter214-qwen35-4b.json`. Storage admitted this job with a 100,000,000-byte unique reservation and included the approved data root, Docker WSL model volume, and automation directory. C: free space was checked above 5 GiB. Recheck status and RAM/VRAM before run and monitor in-process; at least 10% RAM and VRAM must remain free. Run only the exact pinned local environment with offline model loading and Python socket blocking. Do not contact SubRoute/providers, access credentials, use real repositories, or open held-out data.

A verifier failure, resource breach, changed identity, missing provenance/evidence, output collision, or telemetry error is recorded as failure/incomplete; do not tune or retry beyond the runner's existing bounded policy. Keep the candidate inactive. This pair cannot establish the 95/5/95 product gates, Frontier savings/cost, model-size winner, LoRA utility, or all-day engineering.
