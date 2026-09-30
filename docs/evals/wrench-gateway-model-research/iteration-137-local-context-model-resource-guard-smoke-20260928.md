# Iteration 137: guarded local context and model smoke

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-LOCAL-CONTEXT-RESOURCE-GUARD-ITER137`  
Status: **one synthetic lookup completed; resource guard did not breach**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Episode and result

The provider-free local runner prepared one authored synthetic code-symbol retrieval episode through deterministic Wrench E0, then asked the pinned Qwen3.5-0.8B base model to return the function identifier. The exact identifier verifier passed: `calculate_retry_delay`. The two required source quotes remained visible in prepared context.

The target prompt tokenizer counted 6,439 baseline input tokens and 597 prepared input tokens, a 90.728374% reduction. This is prompt-input mechanics for one synthetic case. The model runtime itself reported 481 input and 6 output tokens. It made no frontier calls; frontier-token savings and all-in-cost savings are undefined because there is no paired frontier-only arm.

| Measurement | Observed |
|---|---:|
| Verified synthetic lookup | 1/1 |
| Required quotes visible | 2/2 |
| Target prompt input tokens | 6,439 to 597 |
| Target prompt input reduction | 90.728374% |
| Local model input/output tokens | 481 / 6 |
| Frontier calls / provider spend | 0 / $0 |
| Frontier-token / all-in-cost savings | Undefined / undefined |
| Total runtime | 18.43 s |
| Model loading / generation | 6.7311 s / 4.8178 s |
| Minimum sampled free RAM | 14.0801% |
| Minimum sampled free VRAM | 82.6068% |
| Resource guard breach / generation abort | No / No |

The run began at 17.1657% free RAM and 15,129 / 16,311 MiB free VRAM, and ended at 14.0529% free RAM and 13,477 / 16,311 MiB free VRAM. The sampler collected 14 samples with no telemetry error.

## Exact identities

| Item | Identity |
|---|---|
| Model | `Qwen/Qwen3.5-0.8B` |
| Model revision | `2fc06364715b967f1860aea9cf38778875588b17` |
| Model inventory SHA-256 | `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519` |
| Snapshot verification receipt SHA-256 | `6fa3726115fcd4c9fe2939ed4f0f2b75347ca20a9de701c580cbbf5368f2f8a6` |
| Episode fixture SHA-256 | `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1` |
| Prepared prompt SHA-256 | `b2707155a038d6e0a729c06436536b378f1f55c24cb8be18d004d45556acff7e` |
| Snapshot SHA-256 | `af48e57bd07efcc003935c952be5f1685913acd719840f301d26b7f2a9f8a77c` |
| Receipt | `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\local-model-resource-guard-iter137.json` |

Runtime was NVIDIA GeForce RTX 5060 Ti, BF16, CUDA 13.2, PyTorch 2.14.0+cu132, Transformers 5.17.0, Python 3.13.15. The run used no adapter. The receipt binds source hashes for the runner and Wrench context pipeline components.

## Preserved setup failure

The first smoke attempt, Iteration 136, exited before model loading because its invocation omitted the pinned `WRENCH_LORA_ADDONS` environment path and could not import `accelerate`. It produced no model output or result receipt. This is a setup failure, not a model failure. Its bounded 100,000,000-byte storage reservation was released after confirming the process had exited and no receipt existed. Iteration 137 reran with the pinned add-ons path and completed. Iteration 135's resource guard implementation and three focused unit checks are documented in [the preceding report](iteration-135-local-model-resource-guard-20260928.md).

## Admission, costs, and limits

Iteration 137 reserved `100,000,000` bytes before inference. It used the locally pinned model and made no provider request; provider spend was $0. This does not mean hybrid all-in cost is zero. Storage was scanned with the approved data root, SubRoute, the active worker checkout, the hourly automation directory, and Docker's WSL model volume included. The final pre-release scan was `WITHIN_LIMIT`: 15,436,306,187 actual bytes plus 131,103,000 bytes of active reservations, for 15,567,409,187 projected bytes against the 50,000,000,000-byte ceiling. The C: volume retained more than 5 GB free.

This single authored lookup does not establish coding success, LoRA behavior, full-context task-success retention, 95/5 routing quality, frontier-token savings, all-in cost savings, or all-day engineering reliability. It is not a basis to choose 0.8B as the overall best model. The updated model-size decision remains the size-selection evidence; a larger candidate still requires fresh pinned inventory, license/runtime compatibility, storage admission, and resource gates. The full product acceptance claims remain active and unproven.
