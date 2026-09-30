# Iteration 163: Qwen3.5-4B offset-map monotonicity diagnostic

- Job ID: `WRENCH-QWEN35-4B-OFFSET-MONOTONICITY-DIAG-ITER163-20260928`
- Scope: local offline fast-tokenizer only over 256 approved synthetic train rows and 64 approved synthetic dev rows. No model load, generation, optimizer step, held-out payload, provider request, or disk output from the diagnostic.
- Tokenizer identity: pinned local tokenizer for `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.

## Result

Across all 320 full serialized rows, the returned offset mappings had:

| Check | Observed |
|---|---:|
| Rows | 320 |
| Decreasing start offsets | 0 |
| Decreasing end offsets | 0 |
| Overlapping nonzero spans | 0 |
| Zero-length spans | 0 |
| Out-of-range spans | 0 |
| Maximum sequence length | 338 tokens |

This supports the trainer's added range and start/end monotonicity checks for this exact synthetic split and tokenizer identity. It is not a general guarantee for other tokenizers, data, or production inputs. Attempt 03 still requires its source-reviewed one-step preflight; these counts do not prove the actual trainer succeeds or that a LoRA improves behavior.

Resources during the diagnostic stayed above the required floor: final sample RAM free 26.03%, RTX 5060 Ti VRAM free 15,218/16,311 MiB. The reviewer separately confirmed the source changes at exact hashes in the Iteration 163 source-review report.
