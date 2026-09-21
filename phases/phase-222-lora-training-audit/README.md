# Phase 222: LoRA training pipeline audit

Status: `DEVELOPMENT_DIAGNOSTIC_ONLY`

This phase audits the real Hugging Face LoRA path against the Qwen3.6
8-expert BF16 candidate. It does not use `final.jsonl`, and it does not
promote a checkpoint for release.

## Findings

- The prompt and target label boundary was rewritten to concatenate token IDs
  directly. This avoids relying on re-tokenization across the chat-template
  and JSON boundary.
- The tokenizer boundary check passed for all 132 calibration rows.
- A 2-row, 4-step sanity checkpoint generated 2/2 exact targets.
- An 8-row, 32-step overfit checkpoint generated 7/8 outcome matches and 6/8
  exact targets.
- Full 132-row calibration at 512 steps reached 30/44 development outcome
  matches and 16/44 exact targets after fused-runtime evaluation.
- Full 132-row calibration at 1,024 steps reached 30/44 development outcome
  matches and 16/44 exact targets. This improved over the earlier 100-step
  result of 26/44 outcome matches and 10/44 exact targets, but remains far
  below the production target.
- The independent verifier remained in the loop. No result in this phase is
  a final quality, safety, MiniMax-parity, or release claim.

## Runtime note

The isolated Python 3.11 environment uses Torch 2.9.1+cu128 and Transformers
5.17.0. Installing `triton-windows==3.8.0.post28` enabled the Qwen gated
delta-rule fused path after first-run JIT compilation. A warm one-case smoke
fell from 35.268 seconds to 4.628 seconds. `causal-conv1d` could not be built
because the Windows host has no `nvcc`, so that path still falls back to the
reference implementation.

## Decision

More LoRA steps alone are not sufficient. The remaining errors are concentrated
in long path copying, patch diff copying, and exact boundary abstention. Keep
this candidate diagnostic-only and prioritize a structured mechanical toolbelt
or a training/data design that explicitly improves those fields before any
release selection.

