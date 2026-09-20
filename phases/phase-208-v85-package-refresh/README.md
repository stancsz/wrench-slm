# Phase 208: v85 package refresh after Ollama boundary

Date: 2026-09-20

The portable package was rematerialized after the Ollama validation boundary
was recorded in the source manifest and materializer.

Package:

`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v85-ollama-boundary`

The package contains both the embedded hybrid context gate and the explicit
Ollama backend status:

- fast gate: 4M raw input to 64K effective working context;
- dense-native conditional gate: 32K to 64K target;
- Ollama 0.34.2 MLX import and 4M metadata: verified;
- native Ollama generation quality: failed on validation host.

Structural validation passed. A fresh package-local Ollama-shaped 4M handoff
also passed with 3,999,942 raw estimated tokens, 1,955 staged tokens,
101.524 ms server staging, and 220.408 ms complete local protocol-stub round
trip.

This is the current honest portable artifact boundary. It does not claim
generic vLLM loading or usable stock-Ollama NVFP4 generation.

Receipts:

- `phases/phase-208-v85-package-validation.json`
- `phases/phase-208-v85-handoff-api-chat.json`
