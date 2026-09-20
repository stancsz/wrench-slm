# Phase 93: native skip tuning and attention LoRA probe

Status: experiments recorded, no promotion.

## Native direct context

The serving probe now loads the package tokenizer with `trust_remote_code=True`
and the native serving script accepts the explicit `none` full-attention policy.
This fixes two benchmark-entry defects without changing model weights.

With the complete raw prompt sent directly to the FreeToken endpoint:

| Probe | Actual prompt tokens | Truncated | Elapsed |
| --- | ---: | --- | ---: |
| 1M aggressive skip, 950K layers skipped | 999,915 | no | 81.161 s |
| 4M aggressive skip, 3,967K layers skipped | 3,999,939 | no | 199.177 s |

Both returned HTTP 200 and passed the direct-input token-count gate. The 4M
variant is slower than the earlier 129.291 s history-skip diagnostic, so this
more aggressive suffix policy is rejected as a default. These are intake and
latency measurements, not native retrieval-quality evidence.

## Attention LoRA

The calibration tool now has an opt-in `--attention-lora` mode. It attaches
rank-8 adapters to the Q/K/V/O projections of the 10 full-attention layers and
keeps the existing router and output-head adapters. The 600-step BF16 probe
used 4,460,544 trainable parameters, reached final loss `0.0001005461`, and
remained well under the 4.25B total-parameter ceiling.

On the same 44-case unseen split, with mechanical fast path disabled:

| Arm | Correct outcomes | Correct eligible accepts | Prohibited accepts | Transport failures |
| --- | ---: | ---: | ---: | ---: |
| safe head-only LoRA v1 | 16/44 | 6/24 | 0 | 7 |
| attention LoRA v1 | 15/44 | 3/24 | 1 | 2 |

The attention adapter is rejected. Low training loss did not translate into
workflow quality or safety. The checkpoint is local only and is not published.

## Evidence

- `native-1m-aggressive-skip.json`
- `native-4m-aggressive-skip.json`
- `final-eval-attn-lora-v1.json`
- `phases/phase-92-safe-teacher-calibration/README.md`

The public Hugging Face package is unchanged. The practical path remains the
embedded deterministic route plus bounded staged prefill, while native direct
4M remains experimental until retrieval quality and latency both pass.
