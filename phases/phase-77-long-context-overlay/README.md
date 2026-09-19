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
`truncated: false`, HTTP 200, and `native_context_pass: true`. The probe used
`WRENCH_SWA_WINDOW=8192` to keep the reference run bounded, while the policy
manifest retains the 65,536-token SWA target for the intended overlay. Elapsed
time was 244,524.717 ms, or about 267 input tokens/s. This is native context
correctness evidence for the 8K probe configuration, not a release-speed claim
or a proof of the 65K SWA target. The torch-only MoE copy fallback is a
reference path and is too slow to serve as the final portable backend.

The earlier 256K attempt with the 65,536-token window was stopped after the
same backend showed unacceptable latency. No 2M or 4M native performance claim
is made by this phase. The mechanical 4M-to-effective-context reducer remains
the practical fast path while native attention is optimized separately.

The 4M-configured NVFP4 candidate also loaded successfully with Triton NVFP4
experts and a roughly 428K-token KV allocation. A warm repeated 16K native
probe passed with 16,318 actual prompt tokens, no truncation, HTTP 200, and
6,021.138 ms elapsed. Its cold offload chunks measured roughly 28 to 67 input
tokens/s, so it is still not a release-speed path. FreeToken rejects
`moe-strategy=fused` for NVFP4 experts, which leaves offload or CPU as the
available serving choices on this runtime.

The native probe tool was also fixed to tokenize only one prompt unit when
building large synthetic payloads. The model endpoint's reported
`usage.prompt_tokens` remains authoritative. This removed an approximately
200-second self-inflicted tokenizer delay from the 16K measurement and is
required before trusting 2M stress timings.

Receipts: `long-context-overlay-policy.json` and
`native-64k-swa8k-rerun.json`, plus
`native-16k-nvfp4-swa8k-fastprobe.json`.
