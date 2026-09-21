# Phase 307: clean release candidate package

This phase validates a freshly materialized candidate from a clean detached
worktree at commit `e83a454f85be6881e989c9453291ef35d0b97429`.

The candidate is an experimental portable artifact. It is not a production
release, a learned MiniMax parity result, an independent RTX 5060 Ti result,
or proof of dense native 4M attention quality.

## Passed local receipts

- `validation.json`: structural package validation passed. The config declares
  a 4,000,000-token input context and the two weight shards were hash checked.
- `core-alignment.json`: all eight source-to-package runtime pairs matched the
  clean source snapshot.
- `smoke.json`: HF-shaped package mechanical smoke passed with zero model calls.
- `ollama.json`: the package-local Ollama-shaped route accepted a real
  3,995,426-token payload, returned HTTP 200, and reduced it to 9 effective
  working tokens. The gate measured 25.476 ms and the complete subprocess
  route measured 259.62 ms.
- `portable-client-acceptance.json`: OpenCode, DeepSeek Harness, and Claude
  Code all completed a read-only request with zero model calls and no mutation
  claim.

## Interpretation

The current product path is deterministic intake, lookup, pruning, and bounded
mechanical execution. This proves local package wiring and the 4M raw-payload
acceptance path. It does not yet prove the learned model's quality on the
sealed evaluation set, the 220-case teacher comparison, MiniMax parity,
independent 5060 Ti verification, or production readiness.
