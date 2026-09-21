# Phase 220: hard 4M model-local input boundary

Date: 2026-09-20

The package-local server now enforces the declared 4,000,000-token logical
input limit instead of exposing it only as metadata. It rejects invalid or
larger `options.num_ctx` values and rejects raw input whose bounded estimate
exceeds the same limit.

Verification:

- v91 portable package structural validation: `PASS_STRUCTURAL_PACKAGE`;
- valid direct `/api/chat`: `3,998,332` raw estimated tokens;
- valid round trip: `84.482 ms`;
- valid result: accepted bounded `read_file` proposal;
- model calls: `0`;
- first-layer stage: `mechanical_fast_pruner_cherrypicker`;
- raw payload hash binding: `true`;
- `options.num_ctx=4,000,001`: HTTP `400`.

This turns the 4M claim into a real model-local admission boundary. It does
not claim dense native 4M attention quality or stock Ollama native generation.
