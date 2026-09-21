# Phase 212: Integrated first-layer context gate

Date: 2026-09-20

The source runtime now exposes `FirstLayerContextGate` in
`src/wrench_harness/prefill.py`. The worker uses it for every dynamic native
prefill before a model backend sees the staged messages.

The gate is deterministic and model-local. It accepts the complete raw
message sequence, preserves newest intent and recent hot state, cherrypicks
bounded exact-match evidence from old references, and keeps the original raw
payload hash-bound. Its receipt records:

- raw input token estimate;
- effective working-context tokens;
- selected hot spans and reference cards;
- omitted reference spans;
- the `first_model_side_pruner_cherrypicker` stage identity;
- gate latency and raw-hash binding.

The default budget remains 64K effective tokens, split into 48K hot context
and 16K reference cards. The declared logical input limit remains 4M tokens.
This is the runtime implementation for the conditional dense-native first
layer and the default fast hybrid path. It does not claim that stock Ollama
can execute the Qwen3.5 native checkpoint.

Verification: `pytest -q tests/test_prefill.py tests/test_wrench_server.py`
returned `23 passed`.

The refreshed v86 package also replayed the full 220-case diagnostic suite with
the isolated health fixture and the client mechanical bypass disabled:

- weighted mechanical coverage: `96.2576%`;
- net frontier-token savings: `96.1611%`;
- Wrench plus identical MiniMax fallback final success: `99.6767%`;
- teacher-only final success in this trace capture: `70.7422%`;
- median / p95 latency: `183.378 ms` / `335.241 ms`;
- frontier tokens: `2,487` versus teacher `64,785`;
- prohibited accepts: `0`;
- unexpected mutations: `0`.

Receipt: `phases/phase-212-first-layer-context-gate/replay-220/evaluation.json`.
This remains diagnostic workflow evidence, not family-disjoint approval or
production enablement.
