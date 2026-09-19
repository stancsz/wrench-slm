# Phase 77: zero-global sliding-window native overlay

Status: `PASS_POLICY_NATIVE_64K_REFERENCE_SLOW`

The long-context overlay now supports `WRENCH_GLOBAL_FULL_LAYERS=none`. On the
Qwen3.5 configuration, the verified policy resolves the 30 linear-attention
layers unchanged and the 10 gated-attention layers to a 65,536-token sliding
window. This removes the single global full-attention layer that caused the
previous reducer-bypassed 1M probe to remain saturated.

The policy was resolved by the real FreeToken config parser and then exercised
with the BF16 model on the current Windows FreeToken installation. The runtime
needed two compatibility fixes: expose the installed pinned extension beside
the editable checkout, and use a torch-only per-bank copy fallback when the
host has no CUDA toolkit for FreeToken's optional JIT kernel.

The direct 64K probe completed with 65,448 actual model-side prompt tokens,
`truncated: false`, HTTP 200, and `native_context_pass: true`. Elapsed time was
244,524.717 ms, or about 267 input tokens/s. This is native context correctness
evidence, not a release-speed claim. The torch-only MoE copy fallback is a
reference path and is too slow to serve as the final portable backend.

The earlier 256K attempt with the 65,536-token window was stopped after the
same backend showed unacceptable latency. No 2M or 4M native performance claim
is made by this phase. The mechanical 4M-to-effective-context reducer remains
the practical fast path while native attention is optimized separately.

Receipts: `long-context-overlay-policy.json` and
`native-64k-swa8k-rerun.json`.
