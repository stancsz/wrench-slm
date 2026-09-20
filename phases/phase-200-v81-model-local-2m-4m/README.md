# Phase 200: v81 direct model-local 2M and 4M intake

Date: 2026-09-20

## Receipt

The v81 bundled package's own OpenAI-compatible local endpoint accepted full
raw payloads directly, without an external gateway:

- 2M: HTTP 200, `2,000,010` prompt tokens, 85.855 ms;
- 4M: HTTP 200, `4,000,010` prompt tokens, 171.495 ms;
- raw payload characters: 16,000,075 and 32,000,075;
- backend: `embedded-mechanical`;
- model calls: `0` for both;
- mechanical route: `true` for both.

The package manifest reports `3,881,244,016` parameters against the
`4,250,000,000` ceiling, declares 4M input context, and defaults to a 64K
effective working context.

The raw receipts are `model-local-2m.json` and `model-local-4m.json`.

## Boundary

This proves direct package-local raw intake plus embedded mechanical reduction.
It is not a claim that every raw token receives dense attention, nor a claim
of learned MiniMax parity or production enablement.
