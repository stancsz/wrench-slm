# Phase 219: v90 current portable package

Date: 2026-09-20

The HF-facing package README was refreshed to match the current v88 evidence
and the hybrid product boundary. A new v90 package was materialized from the
same Safetensors source with the current bundled runtime and documentation.

Verification:

- structural package validation: `PASS_STRUCTURAL_PACKAGE`;
- verified parameters: `3,881,244,016`, below the `4.25B` ceiling;
- declared raw input context: `4,000,000` tokens;
- direct package-local 4M `/api/chat` smoke: `3,998,332` estimated raw tokens;
- round trip: `87.064 ms`;
- backend: `embedded-mechanical`;
- model calls: `0`;
- first-layer stage: `mechanical_fast_pruner_cherrypicker`;
- raw payload hash binding: `true`;
- proposal: bounded `read_file` for `wrench-package.json`.

The package README now clearly distinguishes the verified hybrid model-local
path from stock Ollama native generation, GGUF, vLLM, dense native attention,
and final production authorization.
