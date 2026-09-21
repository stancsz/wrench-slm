# Phase 214: Mechanical first-layer gate receipt

Date: 2026-09-20

The model-local mechanical fast path now emits the same first-layer gate
receipt family as the dynamic native prefill path. This makes the actual
production-value route observable as an integrated pruner plus cherrypicker,
rather than leaving the behavior only in package metadata.

For the mechanical lane, the newest intent is the hot span. Historical
messages remain hash-bound and are scanned only for exact bounded lookup or
patch evidence. When the mechanical lane can answer directly, it does not
invoke a model, and the effective working context is the active intent plus
any exact evidence selected by the route.

The receipt is exposed from both `/v1/chat/completions` and the Ollama-shaped
`/api/chat` and `/api/generate` responses. It explicitly keeps
`native_input_claim=false`, so it does not misrepresent hybrid intake as
dense native attention.

Verification:

- `python -m pytest -q`: `168 passed`, `14 warnings`.
- v88 portable package structural validation: `PASS_STRUCTURAL_PACKAGE`.
- v88 package-local 4M raw `/api/chat` smoke, launched from the package's own
  server with no repository `PYTHONPATH`:
  - raw input estimate: `3,998,332` tokens;
  - raw input chars: `7,998,072`;
  - three round trips: `69.658 ms`, `37.463 ms`, `29.749 ms`;
  - backend: `embedded-mechanical`;
  - model calls: `0`;
  - proposal: bounded `read_file` for `wrench-package.json`;
  - gate stage: `mechanical_fast_pruner_cherrypicker`;
  - gate latency: `7.813 ms`, `6.361 ms`, `6.673 ms`;
  - raw payload hash binding: `true`.

This is direct model-local hybrid 4M intake and retrieval evidence. It is not
evidence of dense native 4M attention quality, stock Ollama native generation
quality, family-disjoint approval, or production enablement.
