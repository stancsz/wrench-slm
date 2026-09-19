# Phase 77: zero-global sliding-window native overlay

Status: `PASS_POLICY_RESOLUTION_NATIVE_RUNTIME_BLOCKED`

The long-context overlay now supports `WRENCH_GLOBAL_FULL_LAYERS=none`. On the
Qwen3.5 configuration, the verified policy resolves the 30 linear-attention
layers unchanged and the 10 gated-attention layers to a 65,536-token sliding
window. This removes the single global full-attention layer that caused the
previous reducer-bypassed 1M probe to remain saturated.

The policy was resolved by the real FreeToken config parser without loading
weights. A full native prefill could not be completed on the current Windows
FreeToken installation because its NVFP4/offload path requires the missing
`freetoken.kernel._pinned_tensor` extension. That runtime prerequisite is kept
separate from the attention-policy result.

Receipt: `long-context-overlay-policy.json`.
