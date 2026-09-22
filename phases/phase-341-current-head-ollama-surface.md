# Phase 341: Current-head Ollama-shaped portable surface

Status: `PASS_OLLAMA_SHAPED_MODEL_LOCAL_4M`.

The exact release-line package
`D:\models\_wrench-release-candidate-bbc680f` was started as its own
package-local subprocess and exercised through its Ollama-shaped API surface.
The check did not use an external API gateway.

## Evidence

- Package validation: `PASS_STRUCTURAL_PACKAGE`, two Safetensors shards,
  `config_max_position_embeddings=4,000,000`.
- Ollama-compatible API version: `0.32.13`.
- `/api/tags`: model catalog available.
- `/api/show`: declared context length `4,000,000`; effective working budget
  `64,000`.
- Small local chat: HTTP `200`, accepted, zero model calls.
- Monster local chat: HTTP `200`, accepted, `3,995,426` raw input tokens,
  `35,163,267` raw characters, zero model calls.
- First-layer gate: `27.144 ms`; total monster request: `48.313 ms`.
- Effective working context: `9` tokens, with the raw payload hash bound.
- RAM and VRAM reserve checks passed before and after the subprocess.
- Full repository regression: `196 passed`, `0 failed`, `18` Windows asyncio
  deprecation warnings in `19.14 s`.

This proves the practical model-local portable intake and deterministic
pruner/cherrypicker path. It does not claim dense-native 4M attention quality,
learned MiniMax parity, independent RTX 5060 Ti execution, or production
enablement.

Evidence: `phase-341-current-head-package-validation.json` and
`phase-341-current-head-ollama-surface.json`.
