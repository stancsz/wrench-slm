# Phase 125: Ollama portable runtime boundary

This phase checked whether the public NVFP4 Safetensors package is a
copy-paste Ollama model on Windows, rather than only proving `ollama show` or
model metadata import.

## Observed results

- Ollama `0.32.13` recognized `wrench-4b-native4m-exp:latest` as Safetensors
  with a 4,000,000-token model-side context limit.
- The normal Windows installation failed at completion because the optional
  MLX runner was not installed.
- The matching official MLX bundle was downloaded and run in an isolated
  runtime. The runner detected the RTX 5070 Ti and loaded 3,993 tensors.
- The published checkpoint metadata still declares a Qwen3.5 vision tower,
  while the text-only NVFP4 package intentionally contains no visual tensors.
  Ollama therefore rejected the load with `vision weights are missing from the
  manifest`.
- An isolated no-vision manifest experiment passed model loading and reached
  prefill, proving the metadata mismatch is independently repairable. The
  same run then stopped on the Windows MLX CUDA bundle's hard-coded cuDNN path:
  `C:/Program Files/NVIDIA/CUDNN/bin/x64` was absent.

## Release conclusion

This is a backend compatibility finding, not a model-quality pass. Hugging
Face Safetensors plus the bundled FreeToken path remains the canonical
experimental distribution. Ollama Safetensors completion on Windows is not
yet a verified portable path. A future package should emit text-only config
metadata, then re-run completion on a host with the required MLX CUDA and
cuDNN runtime.

The phase does not claim GGUF support, vLLM support, native attention quality,
MiniMax parity, or production readiness.
