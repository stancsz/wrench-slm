# Phase 365: Ollama-shaped model-local 4M smoke

Date: 2026-09-21

Status: `PASS_OLLAMA_SHAPED_MODEL_LOCAL_4M`

The bundled package's Ollama-compatible model-local surface passed its full
mechanical smoke:

- `/api/version`, `/api/tags`, and `/api/show` passed.
- The declared context length was `4,000,000` tokens.
- Small chat and a `35,163,323`-character monster request returned HTTP 200.
- Monster route elapsed time was `248.549ms`, with hash-bound first-layer
  compaction and zero model calls.
- RAM reserve checks passed before and after the run.

This is an Ollama-shaped local API surface, not proof that the raw NVFP4
Safetensors can be imported by the stock Ollama converter. That separate native
import attempt is recorded in phase 366.
