# Phase 233: corrected real model-local HTTP 4M generation probe

Status: `MODEL_LOCAL_INTAKE_PASS_GENERATION_GAP`

Phase 232 used a 32-token output cap, so it was rerun with 128 output tokens
using the same request, endpoint shape, checkpoint, and nominal 4M input.
The output cap was therefore not the explanation for the generation failure.

The direct package-local HTTP request produced:

- raw input estimate: 3,996,369 tokens;
- HTTP status: 200;
- real Transformers backend;
- staged working context: 2,033 tokens;
- first-layer gate latency: 191.537 ms;
- model calls: 2, including a retry;
- total latency: 27,378.546 ms.

The final assistant output was still malformed and corrupted, so strict
verification did not accept it. This confirms the current learned fallback
quality gap independently of the output cap. The model-local 4M intake and
first-layer reduction are real, but the pure learned path cannot yet be called
MiniMax-parity or release quality. The deterministic mechanical route remains
the owner for the verified routine portfolio.

Evidence: `receipt.json`.
