# Phase 39: balanced 16E calibration

This phase tested whether a lighter safety weighting could preserve the prior
16E task acceptance while removing its one prohibited boundary accept.

Calibration lineage:

- Dataset: `D:\models\wrench-calibration-v8-balanced\train.jsonl`
- Dataset SHA-256: `3e59a0357f9998f0114f1586d6b9c9d9abcc8be00f98d58e047863366b00a34e`
- 224 rows, 300 steps, rank 8, alpha 16, learning rate `5e-4`, seed 17
- Final loss: `0.0005300701013766229`

The packed text-only artifact is
`D:\models\Wrench-Qwen3.6-16expert-profiled-W4A16-NVFP4-calibrated-v5-Balanced-ExplicitSchema-TextOnly-HF`,
at 3,991,755,209 bytes, or 3.718 GiB.

On the identical 28-case unseen fixture, it accepted 4/20 task cases and had
0/8 prohibited boundary accepts. This is worse than the prior 16E pack's 8/20
task acceptance, so it is not promoted. The result supports keeping the prior
16E artifact as the larger experimental tier while further calibration remains
open.

