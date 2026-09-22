# Phase 344: Current-head portable package binding

Status: `PASS_CURRENT_HEAD_PACKAGE_BINDING`.

The package materializer created
`D:\models\_wrench-release-candidate-ae78a84` from the exact repository HEAD
`ae78a84301522de4dfe0745f456090a7dcf8aa36`. Safetensors weights were
hard-linked from the existing immutable package source, so no second 3.2 GiB
weight copy was created.

## Evidence

- Structural package validation: passed.
- Package `config_max_position_embeddings`: `4,000,000`.
- Ollama-shaped model-local surface: passed.
- Monster payload: `3,995,426` raw tokens.
- Monster request elapsed: `45.197 ms`; first-layer gate: `24.983 ms`.
- Effective working context: `9` tokens; model calls: `0`.
- Raw payload hash bound; RAM and VRAM reserve checks passed before and after.

This binds the portable runtime files to the current source HEAD while
reusing the same immutable weight files. It does not claim stock Ollama native
generation, vLLM support, dense-native 4M attention quality, independent RTX
5060 Ti execution, or production enablement.

Evidence: `phase-344-current-head-package-validation.json` and
`phase-344-current-head-ollama-surface.json`.
