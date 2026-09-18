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

## Measured size

| Tier | Retained experts | Actual parameters | Ideal INT4 weight estimate | BF16 directory |
| --- | ---: | ---: | ---: | ---: |
| Compact | 8 | 3,881,244,016 | about 1.84 GiB | `D:\models\Wrench-Qwen3.6-8expert-profiled-BF16-v2` |
| More useful | 16 | 4,888,532,336 | about 2.32 GiB | `D:\models\Wrench-Qwen3.6-16expert-profiled-BF16` |
| Expanded | 32 | 6,903,108,976 | about 3.28 GiB | `D:\models\Wrench-Qwen3.6-32expert-profiled-BF16` |

ModelOpt produced real W4A16 NVFP4 HF exports. The 8-expert artifact is
4,316,262,327 bytes (about 4.02 GiB) and the 16-expert artifact is
4,884,519,327 bytes (about 4.55 GiB). The 16-expert export was also converted
to FreeToken FTW: 4,889,203,342 bytes (about 4.55 GiB), with
`quant_format: nvfp4`, and passed a one-request load/generation smoke. The
larger on-disk size versus the ideal INT4 estimate is expected because this
W4A16 export does not quantize every tensor, and includes runtime metadata.

The 32-expert candidate remains a BF16 structural experiment. Its ideal INT4
estimate is not an actual packed artifact yet.

The provisional calibration corpus remains pending human approval and is not
training or final evaluation data.
