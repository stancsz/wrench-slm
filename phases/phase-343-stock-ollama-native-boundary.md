# Phase 343: Stock Ollama native-runner boundary

Status: `FAIL_OLLAMA_NATIVE_RUN_MLX_UNAVAILABLE`.

The installed stock Ollama client was checked without creating or modifying a
new model. Ollama `0.32.13` recognized an existing Wrench model with a
`4,000,000` context metadata entry, but a bounded real run failed before model
generation because the Windows MLX runner dynamic library was unavailable.

Observed error:

```text
500 Internal Server Error: mlx runner failed: MLX not available: failed to load MLX dynamic library
```

After the failed run, no model remained loaded and the RTX 5070 Ti had about
`15,167 MiB` VRAM free. This does not invalidate the package-local
Ollama-shaped API, which independently passed the 4M raw intake and reducer
probe in phase 341. It does mean stock Ollama native generation is not a
portable Windows claim for this package yet. vLLM and GGUF remain unverified.

This is a backend compatibility boundary, not a dense-native quality result or
independent RTX 5060 Ti evidence.

Evidence: `phase-343-stock-ollama-native-boundary.json`.
