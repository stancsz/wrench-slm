# Phase 205: v83 sealed final replay

Date: 2026-09-20

The v83 portable package was replayed through its own model-local HTTP server
against the sealed `evals/wrench-expanded-v2/final.jsonl` split. The client
mechanical shortcut was disabled and the health dependency used an isolated
loopback fixture.

Results:

- 44 total traces, 24 eligible traces;
- weighted mechanical frontier-token coverage: 100%;
- net frontier-token savings: 100%;
- Wrench-plus-identical-teacher-fallback weighted final success: 100%;
- teacher-only weighted final success: 78.3130%;
- Wrench local tokens: 4,805;
- Wrench frontier tokens: 0;
- median / p95 latency: 186.640 ms / 322.191 ms;
- fallbacks: 0;
- prohibited accepts: 0;
- unexpected mutations: 0.

This is a sealed-split diagnostic receipt. It was not used for training,
LoRA, expert selection, or prompt tuning. It does not establish the required
family-disjoint approval, independent 5060Ti verification, stock Ollama
generation portability, or production enablement.

Receipts:

- `evaluation.json`
- `trace-manifest.json`
