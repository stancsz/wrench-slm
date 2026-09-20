# Phase 120: prompt-complete executable mechanical contract

This phase keeps the historical 220-case fixture unchanged and builds a
derived 220-case contract where every eligible prompt contains enough typed
information to execute the requested bounded operation.

## Contract shape

- 220 total cases;
- 120 eligible cases;
- 20 explicit review-only patch cases;
- 20 health cases with explicit timeout and response bounds;
- the historical boundary and out-of-domain shape is retained;
- the synthetic fixture is a separate temporary Git repository.

## Endpoint receipt

`full-220-endpoint-v3.json` was produced by sending all cases through the
downloaded Wrench v31 OpenAI-compatible endpoint, with the endpoint's own
mechanical receipt propagated through the client:

- 220/220 outcome matches;
- 120/120 exact eligible proposals;
- 220/220 model-local mechanical fast paths;
- 0 model calls;
- 0 prohibited accepts;
- 0 transport/runtime failures;
- median 0.528 ms, p95 37.861 ms, mean 6.284 ms.

`weighted-route-score.json` joins the same case IDs to the approved historical
trace weights for route-coverage diagnosis. It reports 100% eligible case
coverage and 100% eligible frontier-token mass coverage.

This is strong evidence for the bounded deterministic worker and its direct
model-local endpoint. It is not MiniMax parity, native dense 4M retrieval
quality, or production workflow utility. The historical fixture remains
separately reported because its 20 accepted patch targets are not inferable
from their prompts.
