# Iteration 211: in-process CUDA resource telemetry and code-task MVP

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER211-20260929-01`  
Nonce: `cf00ee78-d600-4411-8a6f-23b5c7c7f869`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Difference from Iteration 210

Iteration 210 stopped after the `nvidia-smi` subprocess timed out during first generation, before an answer was returned. This run keeps that receipt immutable. The code-task, fixture, verifier v2, model, decoding limit, pair and single-retry rules remain unchanged. Only run-time resource sampling changes: RAM is sampled through `GlobalMemoryStatusEx`; VRAM is sampled in-process through `torch.cuda.mem_get_info(0)` every 0.5 seconds. The independent `nvidia-smi` check is run immediately before loading and once after generation, never from the monitor thread. A >10 percentage-point pre/post disagreement invalidates the pair. Missing/failed runtime samples or crossing either 10% floor stop generation and produce an incomplete receipt.

## Exact package

- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter211.py`, SHA-256 `19FF90E2B27EC0C1005492B5496C913C6B0985CC45AF16FD694513A0AB6CBD98`.
- Resource tests: `tests/test_gateway_torch_resource_sampler_iter211.py`, SHA-256 `2DF1134364AF0650FC72F579251F140584C02D109116A52323626ED566934F44`.
- Verifier regression tests: Iteration 210 test `tests/test_gateway_code_task_verifier_iter210.py`, SHA-256 `70913467E5C28D4D4EE6DCA71F7EB7BC6C24012F00D1CCF33220ADE1F7462DC8`.
- Output, no-clobber: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\code-task-iter211-qwen35-4b.json`.
- Base model: pinned `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base only; exact inventory, local runtime and GPU checks reuse Iteration 207's pinned identities. Adapter remains inactive.
- Runtime: pinned Iteration 206 environment, Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2, RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.

## Procedure and reporting

Run focused byte-sampler and verifier tests, `git diff --check`, and a no-model telemetry calibration before inference. The calibration measured 28.17% free RAM and 93.19% free VRAM via Torch versus 27.84% RAM and 91.58% VRAM via `nvidia-smi`; the VRAM fraction delta was 1.60 percentage points. Immediately before launching, check fresh resources, no duplicate job/output, C: headroom, and storage status with the 150,000,000-byte reservation for this exact job.

Run one paired synthetic retry-function repair. Wrench must retain the function and TOML cap evidence. Record local prompt/output tokens, both attempts and any retry/recovery, deterministic AST and behavior verification, prompt/snapshot/source hashes, latency, CUDA peak memory, Torch-sampled resource minima, and pre/post `nvidia-smi` cross-checks. Stop if RAM or VRAM free falls below 10%, telemetry fails, identity changes, or the output already exists.

This is a single authored local code task, not a representative coding-success rate or all-day engineering study. Local tokenizer values are not provider usage or Frontier savings. The run forces offline local model loading, blocks Python socket connects, reads no held-out data, calls no provider, and cannot write to the real repository. No training or adapter activation is authorized.

The on-disk goal hash remains different from the hourly heartbeat's stated value `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`. This protocol pins the current file as read; reconcile before any hash-bound fit review.
