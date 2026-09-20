# Phase 82: deterministic boundary router

Status: `DIAGNOSTIC_IMPROVED_NOT_MINIMAX_PARITY`

This phase moves unambiguous invalid requests into the bounded mechanical
router before the local model is called. It covers malformed limits, line
bounds, missing paths, repository-root errors, health endpoint violations,
literal-search mode errors, and invalid patch requests. The router returns the
same stable abstention reason that the independent verifier would use.

## Evidence

The safety-native2M BF16 candidate was replayed against the historical 220-case
fixture at the same local FreeToken endpoint and decoding contract used by the
previous receipt:

- receipt: `wrench-safety-native2m-boundary-router-v2.json`
- outcome matches: `204/220`
- eligible exact proposal matches: `81/120`
- mechanical fast-path requests: `200/220`
- prohibited accepts: `0`
- transport/runtime abstentions: `3`
- median latency: `0.559 ms`
- p95 latency: `5683.262 ms`
- mean latency: `1176.058 ms`

The previous same-host safety-native2M replay was `173/220` outcome matches,
`157/220` mechanical fast-path requests, and `0` prohibited accepts. The
improvement is a routing and boundary diagnostic, not a MiniMax parity result.

## Remaining limitations

The fixture's accepted health cases target `localhost:4000`, but no live health
fixture was running during this replay, so those ten cases remain execution
failures. Patch-draft cases still depend on the model producing a useful
unified diff and are not treated as safe to fabricate mechanically. The suite
is historical regression input, not the approved matched real-workflow trace
set, and does not establish weighted frontier-token coverage, final success,
or production readiness.
