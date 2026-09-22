# Wrench SLM

Wrench is a bounded developer-tool worker for fast, repetitive, verifiable
mechanical work. It proposes structured read-only or review-only actions, or
abstains. An independent verifier and the stronger-model fallback retain final
authority. Wrench does not execute arbitrary shell commands, access
credentials, or write autonomously.

## Active productive-value scope

The project is intentionally narrow. We are keeping and continuing:

1. deterministic mechanical work;
2. independent verification and the no-mutation boundary;
3. hybrid long-context intake and retrieval;
4. the bounded two-state client protocol;
5. OpenCode, DeepSeek Harness, and Claude Code support;
6. latency and timeout repair;
7. one paired real-workflow canary;
8. targeted fallback expansion based on real traces;
9. sustained operational testing.

The North Star is measured productive value against the stronger-model
baseline: final success, safety, successful-task latency, frontier-token use,
local overhead, cost, retries, corrections, abstentions, and fallback.

## Explicitly skipped

RTX 5060 Ti verification, private release packaging as a separate workstream,
learned free-form routing and LoRA optimization, dense-native 4M attention,
stock Ollama or vLLM or GGUF adapters, synthetic replay as a primary milestone,
broad speculative tool expansion, and public production release are out of
scope unless the human product owner changes the goal.

## Current status

The deterministic worker, verifier, hybrid intake, two-state protocol, and
three named client surfaces have current local evidence. The active proof still
requires the paired real-workflow canary, latency and timeout repair, targeted
fallback selection, and sustained operational testing.

Learned routing remains disabled. This repository is an active,
evidence-gated project, not a production release.

## Source of truth

- [GOAL.md](GOAL.md): active goal and North Star
- [COLLABORATION_CONTRACT.json](COLLABORATION_CONTRACT.json): Q4 authority and
  escalation contract
- [docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md](docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md):
  active productive-value evidence contract
- [docs/evidence/README.md](docs/evidence/README.md): evidence map
- [docs/archive/2026-09-22/](docs/archive/2026-09-22/): superseded plans and
  contracts
