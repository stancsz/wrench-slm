# Phase 69: native long-context serving evidence

Status: `4M_DECLARED_4K_DIRECT_PASS_LONG_PREFILL_NOT_ACCEPTABLE`

The standard Safetensors-derived NVFP4 artifact loaded through the local
FreeToken OpenAI-compatible endpoint with `max_model_len=4,000,000` after the
bounded-window runtime patch. A direct 4K request returned model-side
`prompt_tokens=4,010` with no truncation.

The unmodified hybrid attention path rejected direct 2M input at a real KV
capacity of 464,996 tokens. The earlier BF16 path rejected it at 221,150.
Those are runtime limits, not gateway limits.

The bounded-window candidate kept layer 39 global and mapped the other nine
Qwen full-attention layers to a 65,536-token SWA pool. It loaded and served the
4K probe. A 65,536-token direct probe consumed 69,458 prompt tokens and 63
completion tokens but required roughly 365 seconds on the local RTX 5070 Ti
with NVFP4 expert offload. It was stopped as a performance failure, not
claimed as a 4M pass. The accounting receipt was acknowledged after the owned
engine was stopped.

Conclusion: architecture-level bounded KV is necessary, but direct model
prefill is still too slow for the product target. Phase 70 adds the mechanical
cached 4M-to-40K reducer that must run before the expensive first model pass.

