# Phase 174: token-flow accounting for cost evaluation

Date: 2026-09-20

## Purpose

Make the production value measurable as token economics rather than as a
context-window claim. The model-local endpoint now emits a cost-accounting
receipt that separates raw intake from actual model work.

## Evidence

- Full regression: `156 passed, 14 warnings in 34.19s`.
- Endpoint, worker, and client targeted tests: `19 passed` after the change.
- The receipt reports raw input tokens, model prompt tokens, model completion
  tokens, local model tokens, input tokens not sent to the model, repair passes,
  total local elapsed time, and an explicit unpriced-USD state.
- The 220-case runner now aggregates those fields into its summary so a matched
  replay can charge local inference, reducer time, retries, and fallback calls
  against frontier-token savings.

## Boundary

The receipt deliberately does not invent dollar prices. Hardware amortization,
electricity, and stronger-model provider rates must come from the authorized
matched workflow capture. Until those costs are joined, the final 95 percent
net savings gate remains open.
