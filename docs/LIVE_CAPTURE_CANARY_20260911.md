# LeanRouter live-capture canary

Date: 2026-09-11

## Decision

This bounded live canary is a **NO-GO for a token-saving claim**. The capture
and replay plumbing worked, but packaged Wrench-Pro V21 abstained on the
captured read-only tool request. The learned path therefore saved zero
frontier tokens and added 0.834 seconds before fallback.

This was explicitly synthetic traffic through the live production gateway. It
is not a production workload sample.

## Correlated observations

| Measure | Observed |
| --- | ---: |
| Gateway request ID | `69576c56` |
| HTTP result | 200 |
| Route | `base_executor` |
| Served model | `minimax/minimax-m3` |
| Provider prompt tokens | 418 |
| Provider completion tokens | 63 |
| Cached input tokens | 128 |
| Gateway duration | 2.63 seconds |
| Wrench input/output tokens | 162 / 5 |
| Wrench inference duration | 0.834 seconds |
| Wrench action | `ROUTER_FALLBACK` |
| Frontier tokens avoided | 0 |
| Added pre-fallback latency | 0.834 seconds |
| Peak Wrench allocated/reserved VRAM | 1,066,707,456 / 1,132,462,080 bytes |

At the 2026-09-11 OpenRouter price snapshot of $0.30 per million input
tokens, $0.06 per million cached input tokens, and $1.20 per million output
tokens, the observed provider call cost is $0.00017028. The pricing source is
the [official OpenRouter model metadata](https://openrouter.ai/api/v1/models).
This is a calculated cost for one call, not a billing-statement reconciliation.

## Evidence chain

1. LeanRouter production container source matched the host capture source hash:
   `0e579bc9dcd4249f23182d660edb36c332854553f84ea34c575cba489b7aa5cf`
   before the source-class normalization follow-up.
2. The live request was captured with the same request ID as routing, usage,
   completion, and capture events.
3. The frozen two-row source snapshot has SHA-256
   `d999d9d8cd805701a972a1022f0411ce5b02a0ba99782e56901d6f51fd08a586`.
4. Deterministic intake produced 2 rows with 0 rejected rows.
5. Trusted-scenario audit returned `SCHEMA_VALID_NO_PRODUCTION` with 0 errors.
6. The immutable V21 package produced a valid abstention, not a malformed call.

Artifacts are under
`artifacts/trusted-scenarios/leanrouter-capture-20260911-canary2/`.
The versioned price ledger is
`artifacts/trusted-scenarios/price-ledger-openrouter-minimax-m3-20260911.json`.

## Why Wrench abstained

The normal OpenAI tool request exposed a `read_file` schema and a path in the
user prompt, but it did not contain the resource or prior-result structure used
by the frozen selective policy. Inventing that resource would weaken the
runtime boundary. This is a real integration gap: normal gateway requests do
not yet carry enough structured public context for the verified local path.

## Next valid test

Collect naturally occurring tool requests with prior tool observations or add
an explicit, client-supplied public resource field at the gateway boundary.
Then replay only records whose path is visibly authorized by that context. Do
not count prompt-only path extraction as production-safe authorization without
a new frozen policy and evaluation.
