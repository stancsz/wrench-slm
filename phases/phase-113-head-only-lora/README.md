# Phase 113: frozen-backbone head-only LoRA

## Training

The full-backbone LoRA probe was too slow on the 16 GB RTX 5070 Ti. This
experiment cached frozen-backbone hidden states and trained only a rank-16
`lm_head` adapter. It completed on CUDA with 336 rows and 400 steps.

Training receipt: the local checkpoint's `wrench-calibration-receipt.json`.

## Full 220-case result

Receipt: `../phase-113-full-220-head-only-lora/full-220-head-only-lora.json`.

| Arm | Correct outcomes | Exact eligible accepts | Prohibited accepts | Median | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| v7 pure NVFP4 baseline | 51/220 | 3/120 | 6 | 344.246 ms | 878.825 ms |
| head-only LoRA BF16 | 84/220 | 24/120 | 16 | 507.449 ms | 1430.905 ms |

The adapter improves raw task matching but fails the zero-prohibited-accepts
safety gate and is rejected. It is not merged, quantized, published, or used
by the router.

## Next implication

Training must include explicit negative and boundary loss, not just accepted
oracle targets. A future candidate must beat the baseline while keeping
prohibited accepts at zero on the complete 220-case comparison. The current
public package remains the deterministic embedded route plus fail-closed
fallback.
