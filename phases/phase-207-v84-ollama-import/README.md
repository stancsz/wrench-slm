# Phase 207: v84 Ollama import boundary

Date: 2026-09-20

## Import and metadata

Ollama 0.34.2 with the MLX CUDA runtime imported the v84 Safetensors package
through its bundled `Modelfile`:

- model name: `wrench-v84-mlx-import`;
- format: Safetensors;
- family: `qwen3_5_moe`;
- parameter size: 3.4B;
- quantization: NVFP4;
- tensors loaded: 3,993;
- reported context length: 4,000,000;
- `num_ctx`: `4e+06`.

This is a real stock-Ollama-shaped import and metadata result, using the
relocatable local MLX runtime on the RTX 5070 Ti.

## Generation boundary

Native generation quality did not pass:

- `/api/generate`, 16 requested output tokens: `eval_count=16`, empty returned
  text, 13,579.807 ms total;
- `/api/chat`, `think=false`, 64 requested output tokens: `eval_count=64`,
  malformed repeated-token text beginning with `n114...`, 12,038.946 ms total.

The runner reached the model and produced token counts, but the output is not
usable Wrench proposal text. This does not prove the weights are universally
bad. It proves that this Ollama 0.34.2 MLX path is not a release-ready native
generation backend for the current NVFP4 artifact.

## Decision

The package metadata now records Ollama import and 4M metadata as verified,
while recording native generation quality as failed on the validation host.
The embedded Wrench model-local MapReduce endpoint remains the supported fast
path. No claim is made for generic GGUF or vLLM loading.
