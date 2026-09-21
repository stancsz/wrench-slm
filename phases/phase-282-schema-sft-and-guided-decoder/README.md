# Phase 282: schema SFT and guided decoder comparison

Date: 2026-09-21

## Purpose

Move the learned lane beyond the malformed native output by testing two
orthogonal fixes: a broader attention-plus-router/head adapter and optional
JSON grammar-constrained generation. All measurements use the 44-row
development split. The sealed final split was not read.

## Adapter experiments

The existing v11 rank-16 head/router adapter was first replayed:

- calibration: 132 rows
- development outcomes: 24/44
- exact eligible accepts: 9/24
- prohibited accepts: 4
- p50/p95: 5,643.357 ms / 23,264.22 ms

A new rank-8 attention-plus-router/head adapter was trained for 180 steps over
the existing 280-row safety calibration with gradient checkpointing. It used
4,460,544 trainable parameters and preserved more than 10% VRAM during
training. Its development result was:

- outcomes: 23/44
- exact eligible accepts: 4/24
- prohibited accepts: 0
- p50/p95: 4,314.532 ms / 12,624.663 ms

The safety improvement came with unacceptable mechanical coverage loss.

## Guided decoder experiment

The evaluation tool now has an opt-in `--guided-json-schema` path using
`lm-format-enforcer` and a compatibility shim for Transformers 5.16.1. The
constraint was intentionally broad: it enforces a valid proposal object and
bounded field types, but it does not choose the correct path or action.

The base v7 checkpoint with guided decoding produced:

- outcomes: 22/44
- exact eligible accepts: 3/24
- prohibited accepts: 0
- p50/p95: 4,123.565 ms / 15,519.151 ms
- 11 invalid JSON outputs remained because the model hit the generation limit
  while repeating an incorrect field value

The v11 adapter with guided decoding produced:

- outcomes: 24/44
- exact eligible accepts: 9/24
- prohibited accepts: 4
- p50/p95: 7,565.796 ms / 31,504.655 ms

## Decision

Neither adapter nor guided decoding meets the 90% mechanical-worker target or
the zero-prohibited-accept safety gate. Guided decoding repairs some syntax,
but it cannot recover semantic path copying and is too slow for the fast lane.
The deterministic embedded toolbelt remains the production path. The optional
guided evaluator is diagnostic only and is not enabled in the portable package
or native FreeToken launcher.

The next high-value verification is independent 5060Ti execution of the
current package and real OpenCode, Claude Code, and DeepSeek Harness traces.

