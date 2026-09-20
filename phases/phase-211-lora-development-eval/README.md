# Phase 211: CUDA LoRA development evaluation

Date: 2026-09-20

This phase tested whether a real BF16 LoRA checkpoint could improve the
proposal model without touching the sealed final split.

## Training

- Base: `D:\models\Wrench-Qwen3.6-8expert-BF16-native2M-candidate`
- Training split: `evals/wrench-expanded-v2/calibration.jsonl`, 132 rows
- Held-out split used for this phase: `evals/wrench-expanded-v2/development.jsonl`, 44 rows
- Runtime: Python 3.11, CUDA PyTorch `2.9.1+cu128`, Transformers `5.17.0`
- Adapter: rank 8, alpha 16, full-attention q/k/v/o projections plus router rows
- Trainable parameters: `4,460,544`
- Steps: `100`
- Final training loss: `0.01656068116426468`

The 100-step checkpoint is outside Git at:

`D:\models\Wrench-Qwen3.6-8expert-BF16-native2M-calibrated-v2-attn-lora-100-20260920`

## Development result

The model was generated directly, without the mechanical fast path, then
checked by the independent verifier. Receipt:

`phases/phase-211-lora-development-eval/development-v2.json`

- 44 cases
- 26/44 expected outcomes matched
- 10/44 exact target proposals matched
- 11/44 outputs were verifier-accepted
- median generation latency: `3163.878 ms`
- p95 generation latency: `5651.504 ms`

Result: `DEVELOPMENT_GAPS`. This LoRA checkpoint is not promoted. The result
supports keeping learned generation as a bounded fallback while the
deterministic mechanical worker owns the routine lane.

