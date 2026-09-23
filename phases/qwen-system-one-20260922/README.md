# Qwen Binary System One

## Status

This phase has a source implementation and one trained experimental head with
a strict development rescore in `run-v1/`. It does not claim real-workflow
quality or a release gate pass.

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

A run receipt records the checkpoint and head hashes, head size, exact input
limits, resource samples, classification latency including tokenization and
synchronized backbone execution, backbone parameter and allocated VRAM
separately from the added head, held-out eligibility coverage, and unsafe
classifier passes. The trainer rejects calibration and development
template-group overlap and records exact prompt overlaps it excludes.

## Run v1

The head was trained on the frozen checkpoint
`D:\models\Wrench-Qwen3.6-8expert-BF16`. Training used only the calibration
split and development was scored once. Calibration and development had zero
template-group overlap. Twelve calibration rows with exact prompt duplicates
in development were excluded, leaving 100 training rows and 20 held-out
threshold-calibration rows. Both groups were balanced across the two labels.

| Measure | Run v1 |
| --- | ---: |
| Development cases | 44: 24 eligible, 20 labeled abstain |
| Eligible passes | 20 / 24 (83.3% coverage) |
| Unsafe `not_abstain` decisions | 0 / 20 labeled-abstain cases |
| Overall classifier accuracy | 40 / 44 (90.9%) |
| Always-abstain baseline | 0% coverage, 0 unsafe passes, 45.5% accuracy |
| Always-continue baseline | 100% coverage, 20 / 20 unsafe passes, 54.5% accuracy |
| Frozen decision threshold | 0.5 |
| Warm classification p50 / p95 / max | 175.45 / 202.09 / 227.49 ms |
| Serialized head | 23,785 bytes, SHA-256 `e33e28af544be5eaf156ff42dbe47d2098a36939bb4b0cfd0222d378d4ee3b0b` |
| Head parameters / raw parameter bytes | 4,098 / 16,392 bytes |
| Qwen backbone parameter bytes | 7,762,488,032 |
| Added head VRAM allocation | 16,896 bytes |
| Lowest free VRAM / RAM during run | 6,895 MiB / 25.5 GiB |

The 88 timing samples include tokenization, one Qwen text-backbone forward,
the binary head, and the worker classification receipt. The run preserved the
10% RAM and VRAM reserves. `original` and `plain` prompt styles both produced
20/24 eligible passes and zero unsafe passes. Four eligible requests were
conservatively abstained.

Files in `run-v1/`:

- `qwen-abstain-head.json`: checkpoint-bound experimental head.
- `receipt.json`: training, resource, identity, and development receipt.
- `development-predictions.json`: saved decisions for 44 development cases
  under each of two prompt styles.
- `strict-development-rescore.json`: independent accounting from the saved
  predictions, with head hash, case hash, labels, authority, and threshold
  checks.

The head reuses a 7.76 GB parameter backbone, so its 23.8 KB size does not
mean the worker fits below 2 GB VRAM. The classifier experiment made zero
provider calls, updated no backbone weights, generated zero tokens, and did
not read the existing final split. The 220-case suite remains
`DRAFT_PENDING_HUMAN_APPROVAL`; authored development examples do not establish
independent real-workflow value. Production enablement stays disabled and
Gates C, D, and E remain open.
