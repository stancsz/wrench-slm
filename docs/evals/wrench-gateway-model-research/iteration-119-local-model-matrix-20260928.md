# Iteration 119: three-case Wrench plus local model matrix

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-DEMO-LOCAL-MODEL-MATRIX-ITER119`  
Status: **3/3 authored synthetic lookup answers passed deterministic verification; product-level claims remain unproven**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Paired prompt-input and local-answer results

The runner uses the same authored synthetic repository as Iteration 098,
prepares each task through Wrench E0, feeds the prepared messages to the local
Qwen3.5-0.8B base model, and checks an exact expected answer. It made one model
load and three local generations.

| Case | Target baseline input | Wrench input | Input reduction | Local input/output | Generation | Exact verifier |
|---|---:|---:|---:|---:|---:|---|
| Retry policy | 6,448 | 805 | 87.5155% | 775 / 8 | 4.4585 s | Pass |
| Session lifetime | 6,450 | 734 | 88.6202% | 666 / 11 | 3.5831 s | Pass |
| Retry function | 6,439 | 596 | 90.7439% | 484 / 6 | 1.9652 s | Pass |
| **Ratio of sums / total** | **19,337** | **2,135** | **88.958991%** | **1,925 / 25** | **10.0068 s** | **3 / 3** |

All seven required evidence quotes were visible (3 + 2 + 2). The local answers
were exactly `3,250`, `1800,300`, and `calculate_retry_delay`. This establishes
that the base model can answer these three narrow evidence lookups after E0
preparation. It does not compare task success against an uncompressed prompt,
and does not measure provider tokens avoided. The token reduction uses the
pinned MiniMax M3 target tokenizer and measures input mechanics only.

## Identity, runtime, and resource evidence

- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16, no adapter.
- Local hardware/runtime: NVIDIA RTX 5060 Ti, Python 3.13.15, PyTorch
  `2.14.0+cu132`, CUDA `13.2`, Transformers `5.17.0`.
- Model inventory SHA-256:
  `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519`.
- Snapshot-verification receipt SHA-256:
  `6fa3726115fcd4c9fe2939ed4f0f2b75347ca20a9de701c580cbbf5368f2f8a6`.
- Matrix runner SHA-256:
  `59f98834666ca7dfeb25bdbb9edad5280f61c23033cd94ae7996a9532c45536d`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\local-model-matrix-iter119.json`,
  4,599 bytes, SHA-256
  `998b258537dac544592eb0d84bbbe09fb96b4cc9637b6ea58aaf1d15d333866c`.
- Standard output log: 4,813 bytes, SHA-256
  `e14b3b33eafec453e2a16e6abe10513d94900272d2d37fae8ed2cf29088814db`.
- Standard error log: 2,001 bytes, SHA-256
  `0170baadd4761484d63ea52a3d9c6c7c48863d823c314f8c45c1b9b0b95a7bc0`.

The outer watcher sampled 14.18% minimum free RAM across the process; the
in-process watcher measured 14.168%. Minimum free VRAM was 82.13%. Peak CUDA
allocated/reserved memory was 1,666,013,184 / 1,700,790,272 bytes. The 10%
runtime reserve was maintained; the separate Fit-03 training start gate of
25% free RAM was not met. Transformers again fell back to reference kernels
because `causal_conv1d` and `flash-linear-attention` were not installed.

Storage admission was `WITHIN_LIMIT`, 15,433,836,927 actual bytes before the
run plus existing reservations. This job reserved 100,000,000 bytes, included
the Docker WSL model volume and hourly automation directory, and used a C:
volume with more than 140 GB free. Release the reservation only after the
final storage scan counts the receipt, logs, and this report and confirms that
the model process and temporary fixture have stopped.

## Preserved setup failure

Iteration 118 loaded the model but raised `StopIteration` before preparing a
task because the first case mutated the shared task tuple used to look up the
next case. It made no model generation and is not a task failure. Outer samples
were 14.39% minimum free RAM and 82.04% minimum free VRAM. Its stderr is 2,481
bytes, SHA-256
`049b5326e8111d3d64856385327ff2c6a2062557b07828e74c60822393eeb4d5`; stdout
was empty (SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Its
process exited, output was counted, and its separate 100,000,000-byte
reservation was released before Iteration 119.

## Decision

This is useful evidence for a small **mechanical evidence-answering** role,
not for writing patches or all-day engineering. The tested cases are three
synthetic lookups over one fixture containing 240 repetitive log lines. The
88.96% input reduction is below 95%, and differs from the 90.65% Iteration 117
single-case result because the per-case prompts and target inputs differ. Do
not merge the two denominators. No LoRA was trained or loaded, no frontier
call was made, and full-lifecycle frontier-token savings, task-success
retention, 95/5 routing, dollar savings, and sustained engineering remain
unknown.

Next, compare this local arm against deterministic retrieval and test the same
frozen tasks at the best verified context budget. Then return to the reviewed
LoRA candidate only after its exact package is re-reviewed and free RAM reaches
the 25% fit-start gate. Keep SubRoute `:4000` unchanged and provider calls
closed without an enforced numeric campaign cap.
