# Phase 25: Router profiling and two expert-retention tiers

Status: experimental evidence complete for router telemetry, BF16 structural
candidates, and packed W4A16 NVFP4 exports. Quality and release gates remain
open.

The real local Qwen3.6-35B-A3B NVFP4 teacher was profiled through FreeToken
with 20 provisional Wrench prompts covering bounded reads, literal search,
read-only status, health reads, review-only patch drafts, compaction, schema
handling, abstention, and repair. The hook recorded top-k expert assignments,
router entropy, and token counts for 40 routed layers.

The per-layer selection rule is descending activation count with lower source
expert ID as the tie-breaker. The selection receipts keep 8, 16, and 32
experts respectively. The MTP block was not reached by this runtime path, so
it uses the aggregate profile ranking and is called out in each receipt.

## Artifacts

- `router-profile.json`: real teacher activation receipt, 20 requests, 40
  routed layers.
- `selection-8.json`, `selection-16.json`, and `selection-32.json`:
  reproducible per-layer choices.
- `prune-8-receipt.json`, `prune-16-receipt.json`, and `prune-32-receipt.json`:
  streamed BF16 prune
  receipts.
- `runtime-smoke-8.json`, `runtime-smoke-16.json`, and `runtime-smoke-32.json`:
  CUDA load and forward
  receipts. These are structural checks, not quality passes.
- `inspect-8.json` and `inspect-32.json`: checkpoint metadata checks.
- `runtime-quantized-8.json` and `runtime-quantized-16.json`: one-request CUDA
  smokes through the packed quantized artifacts.
- `runtime-quantized-8-text-only-ftw.json` and
  `runtime-quantized-16-text-only-ftw-default.json`: one-request CUDA smokes
  for the final text-only FTW packs in the 3--4 GiB range.

## Measured size

| Tier | Retained experts | Actual parameters | Ideal INT4 weight estimate | BF16 directory |
| --- | ---: | ---: | ---: | ---: |
| Compact | 8 | 3,881,244,016 | about 1.84 GiB | `D:\models\Wrench-Qwen3.6-8expert-profiled-BF16-v2` |
| More useful | 16 | 4,888,532,336 | about 2.32 GiB | `D:\models\Wrench-Qwen3.6-16expert-profiled-BF16` |
| Expanded | 32 | 6,903,108,976 | about 3.28 GiB | `D:\models\Wrench-Qwen3.6-32expert-profiled-BF16` |

ModelOpt produced real W4A16 NVFP4 HF exports. The original multimodal 8-expert
artifact is 4,316,262,327 bytes (about 4.02 GiB), and the original 16-expert
artifact is 4,884,519,327 bytes (about 4.55 GiB). Wrench is text-only, so a
reproducible pack removes only the `model.visual.*` tensors, 333 tensors shared
by both exports. The resulting self-contained FTW artifacts are:

- 8 experts: 3,426,071,712 bytes (about 3.19 GiB), `quant_format: nvfp4`.
- 16 experts: 3,995,579,915 bytes (about 3.72 GiB), `quant_format: nvfp4`.

Both text-only FTW artifacts passed one-request CUDA load/generation smokes.
The larger on-disk size versus the ideal INT4 estimate is expected because this
W4A16 export does not quantize every text tensor and includes runtime metadata.

The 32-expert candidate remains a BF16 structural experiment. Its ideal INT4
estimate is not an actual packed artifact yet.

The provisional calibration corpus remains pending human approval and is not
training or final evaluation data.
