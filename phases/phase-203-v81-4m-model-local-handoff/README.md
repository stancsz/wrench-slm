# Phase 203: v81 model-local 4M staged handoff

Date: 2026-09-20

## Result

The v81 portable package's bundled `wrench_runtime` accepted a direct
4,000,000-token-class request at its model-local Ollama-shaped `/api/chat`
endpoint.
The request was not sent through an external gateway. A local protocol stub
stood in for the expensive backend so the handoff receipt could be inspected
without spending model inference.

Receipt: `handoff-4m.json`

- raw token estimate: 3,999,943
- raw request bytes: 35,199,607
- model-side staged tokens: 1,955
- configured working budget: 64,000 tokens
- compression ratio: 0.000489
- server staging: 141.426 ms
- full local request: 309.808 ms
- model calls: 1 stub call
- backend: `native-upstream-verified`
- raw payload hash and prepared payload hash: recorded
- reference cards: 1
- evidence windows: 1
- native input claim: false

Status: `PASS_NATIVE_HANDOFF_STAGED_4M`.

## Interpretation

This is the intended practical path for Wrench. The model-local package
receives the monster context, performs its embedded MapReduce and lookup
selection, and only then exposes a bounded working context to the model
backend. It is not dense native attention over all 4M tokens, and the local
stub does not establish MiniMax parity. It does prove that the package-level
Ollama-shaped `/api/chat` serving path has the required raw intake, reduction,
hash binding, and effective-context accounting in one request.
