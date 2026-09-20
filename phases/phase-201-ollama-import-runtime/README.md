# Phase 201: Ollama importer and runtime validation

Date: 2026-09-20

## Result

The v81 Wrench Safetensors package can be imported by the Ollama 0.34.2 MLX
importer when the matching MLX CUDA runtime is present. The imported model is
reported as `qwen3_5_moe`, `3.4B`, `nvfp4`, with `context length 4000000` and
`num_ctx 4e+06`. The import created a model with 1603 layers, size
3,423,221,034 bytes, and digest
`e5f6c68d2e7dc1d84b5390bb1d571860060ab02bb5e1fa4c3c1197efefb0a0637`.

This closes the checkpoint-import portion of the Ollama-shaped requirement.
It does not close actual stock Ollama generation on Windows.

## Reproduced runs

1. Installed Ollama 0.32.13 failed during `ollama create` with:
   `missing fp8 block size metadata for tensor
   model.language_model.layers.0.linear_attn.in_proj_qkv.weight_scale`.
2. The standalone Ollama 0.34.2 base binary started on an isolated port, but
   its create path reported that the MLX dynamic library was unavailable.
3. The Ollama 0.34.2 MLX binary plus its extracted `mlx_cuda_v13` runtime
   imported the package successfully and preserved source quantization.
4. A real `/api/generate` request loaded all 3993 tensors and initialized
   `Qwen3_5MoeForConditionalGeneration`, but the MLX worker then failed before
   generation with a panic while scanning the compiled-in path
   `C:/Program Files/NVIDIA/CUDNN/bin/x64`. The path is absent on the current
   development machine. Setting `CUDA_PATH`, `CUDNN_ROOT_DIR`,
   `CUDNN_LIBRARY_PATH`, and `CUDNN_INCLUDE_PATH` to the bundled runtime did
   not change that compiled-in path.

## Interpretation

The weights and Ollama importer are compatible. The remaining gap is a
portable Windows MLX CUDA and cuDNN runtime package or a rebuilt Ollama MLX
binary whose cuDNN path points at the package-local runtime. Until that is
verified, the canonical Wrench product path remains the package-local
model-local endpoint with embedded MapReduce, retrieval, and verification.
The Ollama import result must not be presented as end-to-end Ollama inference
support.
