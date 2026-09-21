# Phase 223: Current-source mechanical 220 replay

Status: `PASS_DIAGNOSTIC_DETERMINISTIC_ROUTE`

The current checked-out source replayed all 220 rows from
`evals/wrench-expanded-v2/cases.jsonl` through `mechanical_route`.

- requests: `220`
- mechanical fast path: `220/220`
- outcome matches: `220/220`
- prohibited accepts: `0`
- elapsed route time: `8.195 ms`
- sealed final split used: `false`

This proves the current deterministic mechanical route, not learned-model
quality, MiniMax parity, full workflow cost savings, dense native attention, or
production readiness. The independent verifier and identical stronger-model
fallback remain required for the product claim.

