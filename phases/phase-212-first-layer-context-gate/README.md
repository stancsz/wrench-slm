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

The v86 directory also passed a direct copy-paste smoke from its own
`run_wrench.ps1`, with no repository `PYTHONPATH`:

- `/api/show`: `context_length=4,000,000`, `parameter_size=3.88B`;
- `/api/chat` accepted `options.num_ctx=4,000,000`;
- an embedded `read_file` proposal returned in `1.003 ms`;
- `model_calls=0`;
- schema, authority, evidence, consistency, blind-critic, and final-gate
  checks all passed.

This proves the portable model-local surface and the sub-4.25B manifest
boundary. It is still hybrid intake evidence, not stock Ollama native
generation quality.
