# Phases 309 to 311: clean candidate 220 replay repetitions

These three runs replay the same current `evals/wrench-expanded-v2/cases.jsonl`
and the same captured teacher response set against the freshly materialized
candidate at `D:\models\_wrench-release-candidate-20260921`.

The suite has 220 rows, including 120 eligible rows, but its manifest remains
`DRAFT_PENDING_HUMAN_APPROVAL`. These are diagnostic regression receipts, not
the final family-disjoint production benchmark.

## Common controls

- Candidate package was materialized from the clean detached source snapshot
  at commit `e83a454f85be6881e989c9453291ef35d0b97429`.
- Cases hash: `da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`.
- The allowlisted health fixture was enabled for comparable latency and
  deterministic health-read behavior.
- All three runs completed 220/220 rows with `PASS_MECHANICAL_WORKER`.

## Repetition results

| Run | Teacher weighted success | Wrench weighted success | Wrench p50/p95 ms | Frontier tokens | Prohibited accepts |
| --- | ---: | ---: | ---: | ---: | ---: |
| 309 | 0.8934198 | 1.0 | 185.822 / 315.441 | 0 | 0 |
| 310 | 0.8934198 | 1.0 | 190.907 / 474.983 | 0 | 0 |
| 311 | 0.8934198 | 1.0 | 184.271 / 307.005 | 0 | 0 |

Each Wrench run used `24,141` local tokens, had zero unexpected mutations,
and reported 100% net frontier-token savings in the diagnostic arm. The
receipts explicitly retain `quality_claim: false` and
`production_enablement: false`.

The no-fixture control is preserved separately in
`phases/phase-308-clean-candidate-220-replay`. It passed the safety gates but
showed a `2321.614 ms` p95 because health reads were not backed by the
allowlisted fixture. That result is not mixed into the controlled repetitions.
