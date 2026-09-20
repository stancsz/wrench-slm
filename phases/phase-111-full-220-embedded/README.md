# Phase 111: full 220-case embedded mechanical route

## Result

The canonical 220-case historical fixture was executed against the downloaded
portable package's embedded model-local endpoint, with the mechanical route
enabled and the deterministic health fixture active.

Receipt: `full-220-embedded.json`.

| Metric | Result |
| --- | ---: |
| Requests | 220/220 |
| Mechanical fast-path requests | 220/220 |
| Correct expected outcomes | 200/220 |
| Exact eligible proposals | 82/120 |
| Prohibited accepts | 0 |
| Transport/runtime abstentions | 0 |
| Median latency | 0.264 ms |
| p95 latency | 55.39 ms |
| Mean latency | 7.329 ms |

## Failure classification

All 20 outcome mismatches are under-specified historical `patch_draft` cases.
The prompt asks for a review-only patch but provides no requested content
change. The embedded route returns `patch_content_missing` instead of
inventing a diff. The other 200 cases match their expected status and reason.

The 38 non-exact eligible proposals are primarily caused by the historical
fixture's expected fields containing numeric health limits that are not present
in the prompt. This is an oracle mismatch, not an execution safety failure.

## Boundary

This is complete embedded-route evidence over all 220 historical cases. It is
not MiniMax parity evidence and does not establish native 2M/4M attention
retrieval quality. The approved matched workflow evaluation remains required.
