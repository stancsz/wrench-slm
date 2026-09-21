# Phase 275: head-only LoRA and model-only diagnostic

Date: 2026-09-21

## Purpose

Separate the embedded mechanical toolbelt result from the neural model result.
The server now has a diagnostic-only `--disable-mechanical-route` switch. The
default remains the embedded, fail-closed route used by the portable worker.

## Calibration

The existing 3.88B BF16 v7 safety candidate was calibrated from the v2
`calibration.jsonl` split only. The sealed final split was not used. The
head-only trainer froze the full backbone and trained a rank-16, alpha-32
lm-head LoRA for 300 steps over 132 rows:

- device: RTX 5070 Ti CUDA
- trainable parameters: 4,005,888
- backbone gradients: disabled
- initial loss: 1.02045
- final loss: 0.00406
- output: `D:\models\wrench-v2-head-only-r16-20260921`

An earlier full-backbone LoRA attempt was stopped when peak VRAM fell to 136
MiB free. It produced no checkpoint and is not a benchmark result. The
head-only route kept approximately 6.5 GiB free during calibration.

## Model-only replay

The calibrated checkpoint was served through the same local OpenAI-compatible
HTTP endpoint with the embedded route disabled. The development split contains
44 rows, including 24 eligible rows. The external receipt is
`D:\models\wrench-v2-head-only-development-20260921-r2.json`.

| Metric | Result |
| --- | ---: |
| Correct outcomes | 18 / 44 |
| Exact proposals | 4 / 44 |
| Exact eligible accepts | 4 / 24 |
| Prohibited accepts | 1 |
| Transport/runtime abstentions | 10 |
| Model calls | 37 |
| Median latency | 4,570.306 ms |
| p95 latency | 10,683.01 ms |

Status: `DIAGNOSTIC_COMPLETE_NOT_MINIMAX_PARITY`.

## Interpretation

This is a real model-only measurement, not an embedded-toolbelt score. It is
far below the 90% mechanical-worker target and fails the zero-prohibited-accept
safety requirement. The current practical value therefore comes from the
embedded deterministic toolbelt plus verifier and fallback boundary, not from
the head-only LoRA alone. No training or model-quality claim is promoted by
this phase.
