# Phase 177: direct 4M-token model-local endpoint

Date: 2026-09-20

## Evidence

The public-v73-equivalent portable package server received a single request
whose local endpoint estimator counted exactly 4,000,000 raw input tokens.

- HTTP status: 200.
- Payload characters: 8,000,037.
- Wire bytes: 8,000,124.
- Wall latency: 66.5 ms.
- Status: `accepted`.
- Backend: `embedded-mechanical`.
- Mechanical fast path: true.
- Model calls: 0.
- Raw input tokens: 4,000,000.
- Model prompt tokens: 0.
- Model completion tokens: 0.
- Local model tokens: 0.
- Input tokens not sent to a model: 4,000,000.
- Local server accounting time: 2.219 ms.
- TTC and verifier gates: passed through the accepted mechanical result.

## Boundary

This is direct model-directory endpoint intake plus embedded MapReduce and
mechanical execution. It is not a claim of dense native 4M attention. The
important production-value result is that a downloaded Wrench package can
accept a 4M-token request without paying model prefill for an eligible routine
task. Native attention remains an optional profile for cases where deterministic
reduction cannot preserve enough evidence.
