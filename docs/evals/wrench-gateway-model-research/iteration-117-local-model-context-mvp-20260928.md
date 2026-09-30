# Iteration 117: local model plus Wrench context MVP

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-DEMO-LOCAL-MODEL-ITER117`  
Status: **one synthetic code-location episode passed with local Qwen3.5-0.8B after Wrench E0 preparation; product claims remain unproven**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Result

This is the first current demo path that runs both Wrench's deterministic E0
context preparation and a local model on one bounded code task. The authored
synthetic repository contains a Python retry helper, configuration, runbook,
deployment settings, and 240 repetitive synthetic health-log rows. E0 retained
the required function source. The local model was asked to return only the
identifier of the function that calculates retry delay.

| Measure | Result |
|---|---:|
| Exact MiniMax M3 target-tokenizer input, full synthetic context | 6,439 |
| Exact MiniMax M3 target-tokenizer input, Wrench E0 context | 602 |
| Target-tokenizer prompt-input reduction | **90.650722%** |
| Required source quotes retained | **2 / 2** |
| Qwen local-model input / output tokens | 490 / 6 |
| Local answer | `calculate_retry_delay` |
| Deterministic exact-answer verifier | **Pass, 1 / 1** |
| Model load / generation / total elapsed | 4.5095 / 4.4438 / 16.0518 seconds |
| Peak CUDA allocated / reserved | 1,624,238,080 / 1,650,458,624 bytes |
| Local model calls / frontier calls / provider spend | 1 / 0 / $0 |

The reduction is prompt-input mechanics measured with the pinned MiniMax M3
chat template. The local model consumes the Wrench-prepared messages using
its own tokenizer. There is no paired frontier-only provider request, so
frontier tokens saved and dollar savings are **N/A**. This single extraction
case is not repository patch success or an estimate of a workload success
rate. The fixture's repeated logs make its prompt-reduction ratio unusually
favorable; the result cannot be generalized from this case.

## Hardware and exact identities

- Hardware: NVIDIA RTX 5060 Ti, 16,311 MiB VRAM; system RAM 32,701.8 MiB.
- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16 on CUDA.
- Model inventory SHA-256:
  `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519`.
- Iteration 080 local snapshot-verification receipt SHA-256:
  `6fa3726115fcd4c9fe2939ed4f0f2b75347ca20a9de701c580cbbf5368f2f8a6`.
- Runtime: Python 3.13.15, PyTorch `2.14.0+cu132`, CUDA `13.2`, Transformers
  `5.17.0`, tokenizers `0.23.2`, huggingface-hub `1.33.0`.
- Demo source SHA-256:
  `b857a6e213614f8ec8988b696a9b7f9d4d52f3fcff617d2e525af964a49e6ee8`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\local-coding-mvp-iter117.json`,
  3,517 bytes, SHA-256
  `8f2b1fd43ca59ba93b01318f7cfc6c42366a24b56c64d52e88a4a1d03c20ddb4`.
- Captured stdout log: 3,662 bytes, SHA-256
  `0bc67f351366f8f7b2e64018a8033c45a9e90bf8eee9b448f24e49c37d34faad`.
- Captured stderr log: 1,797 bytes, SHA-256
  `924b056173684ff3f0e68bbbc61d67a2503f1a056e5f6ef523d6f6ef66049d04`.

The receipt binds the authored fixture, prepared messages, E0 source files,
model inventory, and snapshot-verification receipt by hashes. The model files
were previously checked against the pinned inventory in Iteration 080; this
run did not rehash the complete 1.77 GB model snapshot.

## Resource and storage accounting

The outer process watcher sampled a minimum of 13.88% free RAM over the
process lifetime; the in-process generation watcher sampled 13.66% free RAM.
Both remained above the required 10% floor. The minimum in-process free VRAM
fraction was 82.28%. The completion receipt's post-run sample showed 13.88%
free system RAM and 13,425 MiB free VRAM. No continuous telemetry before model
loading is provided by the Python receipt; the outer PowerShell watcher spans
the complete child lifetime.

Storage status before admission was `WITHIN_LIMIT`: 15,433,756,265 actual
bytes plus 6,103,000 bytes of existing reservations. Job 117 reserved
100,000,000 bytes under the strict 50,000,000,000-byte ceiling. C: had
140,004,438,016 free bytes at the pre-run sample. The run wrote a 3,517-byte
receipt and the bounded logs above; no model was downloaded and no temporary
fixture remains. Release the reservation only after the final storage scan
counts these outputs and confirms the child has exited.

## Failed setup attempts retained

These are engineering setup failures, not model failures, and were not counted
as task attempts:

1. Iteration 114: the PowerShell wrapper passed `-ErrorAction` to `nvidia-smi`
   and parsed its error text as a VRAM reading, then stopped only its own exact
   child. Both output files are empty (SHA-256
   `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). No
   model code or model weights were loaded.
2. Iteration 115: system Python 3.13.15 lacked PyTorch; import failed before
   context preparation or model loading. Stderr is 351 bytes, SHA-256
   `725402eb24faf84495886ea01c9d5ac908525cd807cfeaa3ed545c650a6a1cfd`;
   stdout is empty.
3. Iteration 116: the correct pinned Wrench environment loaded Torch, but the
   separate reviewed add-ons path containing `accelerate` was not on
   `sys.path`. Transformers rejected `device_map="cuda"` before loading model
   weights. Stderr is 1,607 bytes, SHA-256
   `5bc0e7ba1565200df0d9b5adcb9358f439604273b22d3b4e7dacabf04a404cd51`;
   stdout is empty.

Each failed process was confirmed stopped, its output accounted, and its
unique 100,000,000-byte reservation released before the next attempt. The
successful run used the exact training-environment interpreter and explicitly
added the existing approved `WRENCH_LORA_ADDONS` path. Two model kernel
warnings remain: `causal_conv1d` and `flash-linear-attention` were missing,
so Transformers used slower reference PyTorch implementations. This is not an
optimized-throughput or all-day smoothness result.

## Decision and next steps

This improves the size comparison only for a **bounded context/code locator**:
the 0.8B model can perform one exact source-symbol lookup on Wrench-selected
evidence. It does not overturn the provisional Qwen3.5-2B LoRA controller
lead, because there is no paired comparison, trained adapter, or multi-task
measurement. It does not support using 0.8B as a general coding worker. Its
separate 220-token code-generation smoke failed syntax verification in
Iteration 106.

Continue in this order:

1. Run the same frozen multi-case fixture with a deterministic-only arm and
   the 0.8B base, recording every pass, failure, abstention, and token count.
2. Compare the bounded LoRA controller against these arms after its package
   identity is refreshed, independent review passes, and the >=25% free-RAM
   Fit-03 launch gate is met. Keep the held-out split sealed.
3. Evaluate a larger CUDA-capable local coding worker separately. The
   installed 4B Docker CPU-only route did not return a result; it is not a
   verdict about a pinned CUDA host-runtime 4B model.
4. Use the frozen real coding episodes and paired frontier-only arm for
   frontier-token savings, success retention, all-in dollars, and sustained
   engineering. SubRoute `:4000` remains forced to OpenRouter; no provider
   generation was sent because the numeric aggregate spend cap is absent.

The full acceptance target is unchanged: at least 95% verified local
completion, at most 5% frontier-routed episodes, at least 95% of frontier-only
verified success retained, at least 95% fewer full-lifecycle frontier tokens,
at least 95% lower all-in cost, and reliable sustained engineering. None is
established by this iteration.
