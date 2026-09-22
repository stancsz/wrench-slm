# Phase 367: Existing Ollama import runtime boundary

Date: 2026-09-21

Status: `FAIL_OLLAMA_MLX_RUNTIME_WINDOWS`

An existing local Ollama model named `wrench-v84-mlx-import:latest` reports a
4,000,000-token context in its generated Modelfile. A real `/api/chat` request
with a small 4,096-token context failed before generation because the Windows
Ollama MLX runner could not load its MLX dynamic library.

This is separate from the current NVFP4 conversion failure in phase 366. It
shows that an older successful-looking MLX import is not a usable native
Ollama runtime on this validation host. Existing Ollama models were not
modified or removed.
