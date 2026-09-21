# Phase 232: real model-local HTTP 4M probe

Status: `MODEL_LOCAL_INTAKE_PASS_GENERATION_GAP`

The current package-local OpenAI-compatible endpoint was started with the
real CUDA Transformers Wrench worker and the fused rank-8 LoRA checkpoint. A
single request was sent directly to `http://127.0.0.1:28911/v1/chat/completions`
with no external API gateway. The request used the ambiguous development
intent so the deterministic mechanical shortcut could not own it.

Observed receipt:

- raw input estimate: 3,996,369 tokens;
- request body: 35,163,910 bytes;
- HTTP status: 200;
- backend: real `transformers` worker;
- first-layer staged context: 2,053 tokens;
- first-layer gate latency: 181.309 ms;
- model calls: 2, including one retry;
- complete request latency: 10,375.007 ms.

The endpoint and model-local reduction path therefore work for a direct
nominal 4M request. The generated proposal was malformed and did not pass the
strict verifier, so this is not a learned-generation quality pass. The retry
is recorded rather than hidden. It confirms that the remaining gap is output
quality and fallback efficiency, not merely HTTP payload admission.

This receipt does not prove dense-native attention quality or MiniMax parity.
Evidence: `receipt.json`.
