# Phase 58: FreeToken Desktop full-weight comparison

This is a local diagnostic comparison only. It does not enable learned
routing, execution, a pilot, or a production claim.

## Equal conditions

- Runtime: FreeToken `0.1.3+g52322e984` on the same local GPU.
- Server: `127.0.0.1:1919`, text-only, single concurrent request, 8,192-token
  context, 512-token output limit, `memory_ratio=0.7`, MoE offload, Triton
  NVFP4 kernel, and model sampling defaults.
- Fixture: `D:\models\wrench-evaluation-v5-explicit.jsonl`, 28 cases,
  SHA-256 `7ca0ea61fd433bf2dc97ab8f87345de99cd1044e55b96a8c97fa41c2d8f29a05`.
- Prompting and scoring: the same adaptive safety few-shot policy and the
  independent Wrench verifier for every arm.

## Results

| Arm | Accepted | Expected outcomes | Prohibited accepts | Elapsed |
| --- | ---: | ---: | ---: | ---: |
| 8E safety FTW | 10 / 28 | 18 / 28 | 0 | 10.750 s |
| 16E FTW | 13 / 28 | 21 / 28 | 0 | 21.647 s |
| Original full-weight NVFP4 | 12 / 28 | 18 / 28 | 1 | 59.163 s |

The initial 8E invocation was issued before the service finished warmup and
returned only HTTP 503. It was overwritten and excluded from this table. The
three result files above are the completed, post-ready runs.

## Desktop import state

Both candidates were re-packed from their HF safetensors sources into actual
FreeToken FTW directories inside the configured Desktop model library:

- `D:\Users\stanc\.freetoken\models\Wrench-Code-4B-Qwen3.6-8E-Safety-Experimental`
- `D:\Users\stanc\.freetoken\models\Wrench-Code-5B-Qwen3.6-16E-Experimental`

The original full-weight model was served from the existing Desktop library
path `D:\Users\stanc\.freetoken\models\Qwen3.6-35B-A3B-NVFP4`.

These are controlled Wrench-schema diagnostics. They do not measure general
chat quality, authorized real-workflow value, paid-token savings, or production
readiness.
