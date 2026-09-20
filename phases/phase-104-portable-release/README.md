# Phase 104: portable public release verification

This phase records the public copy-paste package boundary after fixing the
bundled toolbelt mapping.

## Result

- Hugging Face repository: `stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M`
- Repository visibility: public
- Canonical format: Hugging Face Safetensors model directory
- Package includes weights, tokenizer hook, worker, OpenAI-compatible local
  server, deterministic prefill, read-only toolbelt, verifier, and FreeToken
  launcher
- GGUF, Ollama, llama.cpp, and vLLM remain explicitly unverified
- Local verification: `116 passed, 8 warnings`
- Local commit: `f7e4ebf`
- Latest public runtime revision: `edafa1e63fd72b7d2c80ee45a635e598d3cbaf10`

This is a public experimental artifact. It is not a production-readiness,
MiniMax-parity, native 4M retrieval-quality, or throughput claim.
