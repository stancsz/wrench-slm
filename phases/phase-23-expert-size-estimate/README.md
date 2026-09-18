# Phase 23: Header-Only Expert Size Estimate

Status: PASS for structural size accounting only.

`tools/estimate_qwen_pruned_sizes.py` reads only safetensors headers from the
official checkpoint at `D:\models\Qwen3.6-35B-A3B`. It does not load tensor
payloads and does not modify the source.

Observed inventory:

- 40 transformer layers plus one auxiliary MoE block in the checkpoint headers
- 256 routed experts per MoE block
- 8 experts selected per token in the original configuration
- 35,951,822,704 BF16 tensor elements, exactly matching the official index
- 33,017,561,088 routed-expert elements and 21,495,808 router elements

Structural scenarios:

| Retained experts per MoE block | Estimated total parameters | Ideal weight-only INT4 size |
| ---: | ---: | ---: |
| 8 | 3.945B | 1.84 GiB |
| 16 | 4.978B | 2.32 GiB |
| 32 | 7.043B | 3.28 GiB |
| 64 | 11.173B | 5.20 GiB |

Keeping 8 experts is the first measured structural candidate inside the
3 to 4B parameter target. This is not yet a selected expert set or a runnable
pruned checkpoint. Quantization scales, alignment, loader support, router
profiling, load/forward parity, calibration, and task quality remain open.
