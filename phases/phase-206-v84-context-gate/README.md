# Phase 206: v84 embedded context-gate contract

Date: 2026-09-20

The portable package materializer now writes the first-layer context gate into
both `wrench-runtime.json` and `wrench-package.json`.

Fast hybrid mode declares:

- 4,000,000 raw input context tokens;
- `first_model_side_pruner_cherrypicker`;
- `mapreduce_dynamic_native` selection;
- 64,000 effective working tokens;
- 48,000 hot-context tokens;
- 16,000 reference-card tokens;
- hash-bound lookup evidence.

Conditional dense-native mode separately declares a pruner/cherrypicker target
of 32,000 to 64,000 tokens, preserving newest intent, authority and
dependency context, recent tool state, and hash-bound lookup evidence. It is
explicitly optional and not a release blocker.

The v84 package was structurally validated and its own Ollama-shaped `/api/chat`
handoff accepted 3,999,942 estimated raw tokens, staged 1,955 tokens, and
returned `PASS_NATIVE_HANDOFF_STAGED_4M`. This run measured 100.293 ms for
server staging and 223.038 ms for the complete local protocol-stub round trip.
The upstream was a local stub, so this validates package wiring and context
accounting, not dense-native model quality.

Receipts:

- `phases/phase-206-v84-package-validation.json`
- `phases/phase-206-v84-handoff-api-chat.json`
