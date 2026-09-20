# Phase 130: balanced boundary attention LoRA

This experiment trained the frozen Wrench BF16 backbone with router updates
and rank-8 attention plus output-head LoRA. The 456-row calibration set was
the development-only balanced boundary set and did not include the sealed
final split.

## Training

- Source: `Wrench-Qwen3.6-8expert-profiled-BF16-calibrated-v7-safety`.
- Steps: 400.
- Learning rate: `0.0003`.
- LoRA rank/alpha: `8/16`.
- Trainable parameters: `4,460,544`.
- Device: RTX 5070 Ti CUDA.
- Final loss: `0.0000704378`.

## Direct 220-case result

The merged BF16 candidate was served by FreeToken with the mechanical route
disabled and evaluated on all 220 historical cases.

| Arm | Outcome matches | Exact eligible accepts | Prohibited accepts | Median | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| top-k=4 direct baseline | 62/220 | 4/120 | 6 | 415.166 ms | 1560.488 ms |
| balanced attention LoRA | 138/220 | 52/120 | 14 | 465.667 ms | 846.779 ms |

The LoRA materially improves proposal matching, but it increases prohibited
accepts and therefore fails the zero-tolerance safety gate. It is not
quantized, published, or promoted. The mechanical route remains the
authoritative fast path while direct generation needs a stronger safety-aware
training objective or an additional deterministic abstention layer.

This result does not prove native 4M retrieval quality, MiniMax parity, or
matched real-workflow utility.

## Evidence

- `full-220-direct.json`.
- Evaluation receipt SHA-256:
  `58E0003F72233887C5750477512D6D714D99AB0644A9380BD5BD4CC1BF16BA7B`.
- Calibration dataset SHA-256:
  `1643cfa6793528cabc831c0f710e3230e0608d5c0d45ee23f35d8e90093395e6`.

