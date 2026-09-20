# Phase 115: accepted plus boundary head-only LoRA

## Training

The calibration set contained 336 accepted oracle rows and 120 synthetic
boundary oracle rows covering path escape, regex mode, external health,
non-allowlisted action, direct patch mutation, and missing file. The backbone
was frozen and only a rank-16 `lm_head` adapter was trained for 500 steps on
CUDA.

## Pure-model 220-case result

Receipt: `../phase-115-full-220-balanced-lora/full-220-balanced-lora.json`.

| Arm | Correct outcomes | Exact eligible accepts | Prohibited accepts | Median | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| v7 pure NVFP4 baseline | 51/220 | 3/120 | 6 | 344.246 ms | 878.825 ms |
| accepted-only head LoRA | 84/220 | 24/120 | 16 | 507.449 ms | 1430.905 ms |
| accepted plus boundary LoRA | 106/220 | 26/120 | 13 | 457.584 ms | 2072.195 ms |

The balanced adapter improves semantic matching substantially, but it still
fails the zero-prohibited-accepts gate. It is rejected and is not merged,
quantized, published, or enabled by the router. The deterministic boundary
route remains authoritative.
