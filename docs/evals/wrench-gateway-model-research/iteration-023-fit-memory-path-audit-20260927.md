# Iteration 023: fit memory-path audit

Date: 2026-09-27

Status: static trainer review complete; no model job admitted

## Why this review

The user authorized the under-10B experiment when the local machine can run it
smoothly. This review checked whether the existing staged GPU LoRA path has an
obvious safe configuration change that would remove its current free-RAM
blocker without weakening the reserve or changing the frozen experiment.

## Trainer path inspected

The pinned screen-02 GPU trainer already:

- fixes `device_map` to the single admitted CUDA device;
- enables gradient checkpointing;
- caps sequence length at 512;
- trains the attention-only profile with 540,672 trainable parameters;
- bounds the fit to 256 synthetic training examples, three epochs, gradient
  accumulation of eight, and exactly 96 optimizer steps;
- enforces a 25% free-RAM fit-start threshold and monitors 10% RAM/VRAM
  minimums throughout the job.

This was a static source review of
[`train_gateway_lora_screen_02_gpu.py`](../../../../tools/train_gateway_lora_screen_02_gpu.py)
and the frozen [fit protocol](lora-screen-02-gpu-protocol-20260927.md). No
runtime package was imported and no model, dataset, or adapter was loaded.

## Current host gate

The latest live resource sample was 3,643.0 / 32,701.8 MiB free RAM (11.14%).
The fit-start threshold is 8,175.45 MiB free; the shortfall is approximately
4,532 MiB (4.43 GiB). The GPU had 15,216 / 16,311 MiB free and 1% utilization.
GPU headroom does not satisfy the separate host-RAM start requirement.

The 25% gate followed a previous full-fit startup that began at 16.70% free
RAM and crossed the 10% hard floor 34.7 seconds later. The existing trainer's
CUDA placement and checkpointing are already the obvious GPU-memory controls;
the reviewed source provides no evidence those settings make a low-RAM start
safe. Lowering the 25% threshold based on current VRAM would therefore be an
unsupported change. No unrelated process was stopped.

## Automation and next action

`wrench-hourly-token-reduction-monitor` remains the single `ACTIVE` hourly
heartbeat for this goal; its duplicate remains paused. Its next run can
recheck resources and continue a bounded independent task. Resume fit-03 only
when a fresh sample reaches at least 25% free RAM and the exact runtime, hash,
storage, disk-space, and held-out isolation checks pass. If this candidate
cannot be admitted on the host, prepare a distinct, fully inventoried
under-10B candidate and its own adapter/runtime/resource gates; do not treat a
paper VRAM estimate as proof it runs smoothly.

No new subagent was spawned for this pass: the decision is a single trainer
gate already covered by prior independent static reviews, and host RAM was
only 1.14 percentage points above the hard operating floor. No Luna advisor
consultation was needed because the local trainer code and exact resource
reading determine the next step.

## Storage and verification

Before this documentation update, storage including
`C:\Users\stanc\github\subroute` was `WITHIN_LIMIT`: 10,991,378,112 actual
bytes plus 6,103,000 active reserved bytes. Documentation job
`WRENCH-HOURLY-TRAINER-MEMORY-AUDIT-20260927-01` reserved 120,000 bytes.
Whitespace, diff, release, and final storage checks are recorded at closeout.
No tests, model execution, download, or provider calls ran.
