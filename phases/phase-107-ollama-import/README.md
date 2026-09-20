# Phase 107: Ollama Safetensors import

Ollama `0.32.13` was tested against the v9 portable package on the RTX 5070
Ti workstation. The bundled `Modelfile` imported successfully with
`ollama create --experimental` and preserved the source NVFP4 tensors.

`ollama show` and the local `/api/show` response reported:

- format `safetensors`
- family `qwen3_5_moe`
- quantization `nvfp4`
- model-side context length `4,000,000`
- capabilities including completion and tools

The actual completion gate did not pass on Windows. Ollama selected its MLX
runner even when an isolated server was started with
`OLLAMA_LLM_LIBRARY=cuda_v12`; the runner failed with `MLX not available`.
The CUDA discovery log did confirm the RTX 5070 Ti and CUDA 12.0. This is a
backend limitation, not evidence that the model weights are corrupt.

The v9 package and `Modelfile` are public at HF revision
`edd25cce711715eca9e819cccc18b0384a3a5a46`.

Ollama's built-in Safetensors quantizer also rejected `q4_K_M`, reporting that
only `int4`, `int8`, `nvfp4`, `mxfp4`, and `mxfp8` are supported. A GGUF or
CUDA completion path therefore remains unverified.

## Boundary

This phase proves public-package import and 4M metadata recognition only. It
does not prove Ollama generation, native 4M retrieval quality, MiniMax parity,
or production readiness.
