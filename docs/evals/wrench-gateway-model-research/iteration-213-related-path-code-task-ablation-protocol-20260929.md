# Iteration 213 protocol: related-path code-task ablation

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER213-RELATED-PATH-20260929-01`  
Nonce: `e4be2407-99d7-42fb-a77e-185cd201ccbe`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`  
Heartbeat-declared goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (does not match the file currently on disk)

## Question

Can deterministic path scoping remove unrelated context from the Iteration 211 code-repair prompt while preserving enough linked implementation and configuration evidence for the exact same model output to pass its deterministic verifier?

Iteration 211 used all five synthetic fixture paths. This ablation restricts only the Wrench-prepared candidate paths to `config/service.toml` and `src/retry.py`, both explicitly identified by the task's subject and configuration dependency. The full-context baseline remains unchanged and still contains all five fixture files. No answer, expected output, or required quote is used to choose the path set. This is a known, previously evaluated synthetic task, so Iteration 213 is a development ablation, not a new independent episode or holdout.

## Frozen comparison

- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter213.py`, SHA-256 `C215AE366FA7B55D6BAA428FB05BFF04F328F5BE74A12511A2C9E648D6DD9639`.
- Task, system/user prompt, model revision, decoding, token cap, AST allowlist, six behavior cases, retry/recovery policy, resource monitor, and full-context baseline match Iteration 211.
- Model: pinned `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base only. No adapter is loaded or activated.
- Baseline arm: full five-path fixture. Prepared arm: Wrench context over only `config/service.toml` and `src/retry.py`. Preserve exact source IDs, hashes, selected references, and required-evidence visibility in the receipt.
- Arm order follows the runner's existing nonce-derived alternation. Each arm allows the existing maximum of one retry; count all retry and recovery prompt tokens. No new prompt or verifier tuning is permitted during this pair.
- Count actual input IDs passed to generation and generated output IDs. Keep the context compiler's target estimate separately, and investigate any mismatch. Report full-lifecycle local-model-token reduction only as a local tokenizer diagnostic, never as Frontier savings.

## Integrity, resource and output gates

Use a distinct no-clobber output path under `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp`. Confirm the expected source, repository HEAD, and on-disk goal hashes before model load. Keep the fixture synthetic, run offline, block Python socket connections as implemented, and do not write generated code to the real repository. Do not call SubRoute, a Frontier provider, or read credentials. Do not access any held-out data.

Before execution, check storage status and reserve the bounded peak under this unique job ID; include `C:\\wrench-slm-data`, the Docker WSL model volume, and this automation directory. Check at least 5 GiB free on C:. Require at least 10% RAM and VRAM free before and throughout inference. Use the in-process sampler and the runner's independent pre/post GPU telemetry cross-check. Abort the pair as incomplete on any source/goal/model identity change, missing required evidence, resource-floor breach, monitor error, output conflict, or verifier failure after its bounded retry.

The 95% completion, <=5% Frontier-routing, >=95% frontier-only success-retention, >=95% full-lifecycle Frontier-token reduction, >=95% all-in-cost reduction, model-size winner, and all-day engineering claims remain unproven. A passing result on this known one-task ablation cannot establish those claims. No training or activation is authorized by this protocol.
