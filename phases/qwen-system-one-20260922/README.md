# Qwen Binary System One

## Status

This phase has a source and training implementation, but no trained head
artifact or run receipt is committed yet. This note does not claim a quality,
latency, or release gate pass.

The implementation is in
[`qwen_abstain.py`](../../src/wrench_harness/qwen_abstain.py),
[`worker.py`](../../src/wrench_harness/worker.py), and
[`train_qwen_abstain.py`](../../tools/train_qwen_abstain.py).

## Contract

- Reuse the configured, frozen Qwen checkpoint and tokenizer.
- Classify as `abstain` or `not_abstain` using one text-backbone forward. The
  classifier does not call the vocabulary projection or generate tokens.
- `not_abstain` only allows the existing proposal and verifier path to
  continue. It does not authorize a tool action.
- The serialized head must be smaller than 1 MiB and must match the exact
  checkpoint and tokenizer identity.
- Inputs contain at most 16 messages and one complete user turn, may include
  system context, and may not include assistant or tool history. The trained
  artifact defaults to a 512 token limit and 8192 character limit. The trainer
  accepts a token limit from 64 through 1024. The runtime loader caps artifact
  limits at 2048 tokens and 16384 characters.
- Media inputs and over-limit inputs abstain for context resolution.
- Local training must preserve at least 10 percent free RAM and VRAM. The
  sealed final evaluation split must not be loaded for training or tuning.
- The trainer fits and calibrates on disjoint template groups within the
  calibration split. It rejects any template-group overlap with development
  and removes exact prompt overlap from the calibration rows before fitting.

## Evidence required

A run receipt must record the checkpoint and head hashes, head size, exact
input limits, resource samples, classification latency including tokenization
and synchronized backbone execution, backbone parameter and allocated VRAM
separately from the added head, held-out eligibility coverage, unsafe
classifier passes, and integration evidence. The trainer rejects calibration
and development template-group overlap and records exact prompt overlaps it
excludes. Authored examples are an experimental checkpoint only. They do not
establish real-workflow usefulness or release readiness.

No training or runtime evaluation was run during this repository cleanup. The
existing final evaluation split was not accessed. Production enablement stays
disabled, and all existing release gates remain in force.
