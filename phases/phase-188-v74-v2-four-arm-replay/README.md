# Phase 188: v74 package on corrected 220-case contract

Date: 2026-09-20

## Contract repair

The generated v2 contract makes the mechanical inputs recoverable without
oracle leakage. Eligible health requests now state their numeric timeout and
response cap. Eligible patch requests now include the exact review-only
unified diff that the proposal must carry. The suite remains 220 cases with
120 eligible, 60 boundary, and 40 out-of-domain rows. Its cases hash is
`77ce67c7b6bb492ffc63ba26c75c322d38d73425f51e672a640705b97c78ac77`, and
offline manifest validation passed.

## Package and teacher receipts

The v74 package is a fresh portable materialization with the deterministic
`localhost` health-probe fix. Structural package validation passed. The
teacher capture is the local MiniMax-compatible endpoint, proposal-only, with
220 requests, zero transport failures, three invalid responses, and
142,988 provider-reported tokens. Its raw capture hash is
`1d5ae50c12bc7ba38d4d2e268b9667f12c85457a08cb2143daab43aa3571908e`.

## Four-arm replay

The current v74 package was replayed through its model-local HTTP endpoint with
the client shortcut disabled:

- evaluator status: `PASS_MECHANICAL_WORKER`;
- weighted mechanical frontier-token coverage: `94.0113%`;
- net frontier-token savings: `100%`;
- Wrench weighted final success: `97.1208%`;
- teacher weighted final success: `76.7929%`;
- Wrench fallbacks: `0/220`;
- Wrench local tokens: `24,141`;
- frontier tokens charged to Wrench: `0`;
- zero prohibited accepts;
- zero unexpected mutations;
- median latency: `184.312 ms`;
- p95 latency: `296.324 ms`.

The trace manifest hash is
`30e6b60ffe62f516ff1a0651d44e6aaee739940ef829ba5906a0556619cedb4d`.

## Boundary

This is the strongest current provider-backed mechanical-worker receipt and it
passes the 90% coverage and 95% savings gates on the corrected contract. It
does not close the final objective by itself: the final family-disjoint trace
set still needs approval and independent 5060Ti verification is pending.
Dense native 2M/4M attention is an optional unverified research lane, not a
release gate for the hybrid Wrench product.
The direct 4M Ollama-shaped MapReduce intake is already separately verified.
