# Phase 373: Current-Head Ollama-Shaped 4M Surface

Date: 2026-09-21

Status: `PASS_OLLAMA_SHAPED_MODEL_LOCAL_4M`

## Scope

The current-head portable package was launched as its own subprocess and
tested through its package-local Ollama-shaped API. This verifies that users
can send a monster raw payload directly to the package endpoint with
`options.num_ctx=4000000`; it does not claim that the stock Ollama binary can
load Wrench's custom NVFP4 checkpoint or that dense native attention is fast.

## Results

- Package: `D:\models\_wrench-release-candidate-59b8b7c`
- `/api/version`: Ollama-compatible
- `/api/tags`: model catalog available
- `/api/show`: declared context length `4,000,000`
- Small `/api/chat`: HTTP 200, zero model calls
- Monster `/api/chat`: HTTP 200, `3,995,426` estimated raw tokens and
  `35,163,323` raw characters
- Monster request elapsed: `278.944 ms`
- First-layer pruner/cherrypicker gate: `27.215 ms`
- Effective working context: `9` tokens in this filler-plus-intent probe,
  within the declared `64,000` working budget
- Raw payload hash binding: passed
- Model calls: `0`
- RAM and VRAM reserve checks: passed before and after

The API surface is therefore directly model-local and Ollama-shaped. The
package remains a hybrid MapReduce route: old material is reference-only,
recent intent is hot, and expensive model work is bounded. The receipt keeps
dense-native quality, learned MiniMax parity, independent RTX 5060 Ti
verification, and production readiness as unauthorized claims.

## Receipt

- External receipt: `D:\models\wrench-phase-373-current-head-ollama\receipt.json`
- SHA-256: `92c31a2e9cdf3abc721da1a09a8b6bb97a96f42c8a0984a05e47c67b9809c529`
