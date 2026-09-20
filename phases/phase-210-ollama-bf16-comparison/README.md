# Phase 210: Ollama BF16 comparison

Date: 2026-09-20

This is a local diagnostic comparison for the dense-native question. It is
not a portable release artifact and it does not change the hybrid Wrench
product gate.

## Artifact and import

- Source: `D:\models\Wrench-Qwen3.6-8expert-BF16-native2M-candidate`
- Approximate source size: `7,890,602,872` bytes
- Local Ollama model: `wrench-bf16-2m-mlx`
- Runtime: patched, relocatable Ollama 0.34.2 MLX on the RTX 5070 Ti
- Import result: passed, `1045` tensors imported
- Reported architecture: `qwen3_5_moe`
- Reported parameter count: `3,944,893,440`
- Reported context length: `2,000,000`
- Modelfile setting: `PARAMETER num_ctx 2000000`

The import and metadata path therefore work for this BF16 comparison. This
does not establish native generation quality.

## Generation check

The request was a short deterministic chat prompt asking for exactly one word,
with `think=false`, `num_ctx=4096`, `num_predict=32`, and temperature `0`.
The MLX runner initialized and loaded the tensors, but the request did not
return a usable completion. The server eventually returned HTTP 500 after
approximately `63` seconds. Runner logs stopped during prompt processing and
also reported unavailable custom CUDA kernels for the Qwen depthwise/gated
delta operations.

Result: `IMPORT_PASS_NATIVE_GENERATION_TIMEOUT_OR_FAILURE`.

This comparison does not prove that the BF16 weights are semantically bad. It
does show that changing NVFP4 to BF16 alone does not make the current native
Ollama/MLX path production-ready on this host. The fast first-layer
pruner/cherrypicker or the hybrid deterministic MapReduce path remains the
required way to avoid dense full-context prefill.

## Boundary

The current Wrench product claim remains the model-local hybrid path: accept
raw input up to 4M, mechanically reduce it to bounded effective working
context, then run proposal semantics and independent verification. A dense
native lane may be added only if the model itself includes the low-cost first
layer that compacts the raw sequence to 32K to 64K before expensive attention,
with hash-bound selection receipts and real proposal-generation evidence.

