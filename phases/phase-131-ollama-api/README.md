# Phase 131: package-local Ollama API and 4M raw input

The portable Wrench package now exposes Ollama-shaped local endpoints from the
same downloaded model directory:

- `GET /api/tags`
- `GET` and `POST /api/show`
- `POST /api/chat`
- `POST /api/generate`

The implementation is an API compatibility layer inside Wrench. It does not
claim that stock Ollama can load the Wrench hybrid checkpoint or that a generic
GGUF conversion preserves the embedded toolbelt.

## Package smoke

Package: `Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v44-ollama-api`.

- Structural package validation: PASS.
- Safetensors shards: 2.
- Declared input context: 4,000,000 tokens.
- `POST /api/show`: reports context length 4,000,000.
- `POST /api/chat` with `options.num_ctx=4000000`: accepted.
- One monolithic payload estimated at 3,999,998 tokens: accepted.
- Latest intent recovered: `read_file` for `README.md`.
- Backend: `embedded-mechanical`.
- Model calls: 0.
- End-to-end package-local response: 5.779 ms.

This is the requested model-local 4M intake path with a fast deterministic
worker. It is not dense native attention over 4M tokens, and it does not close
the MiniMax matched-workflow or production-quality gates.

## Evidence

- `portable-package-v44-validation.json`.
- `ollama-api-4m-smoke.json`.

