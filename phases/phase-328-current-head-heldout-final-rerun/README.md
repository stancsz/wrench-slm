# Phase 328: Current-head held-out final slice rerun

Status: `PASS_MECHANICAL_WORKER`, diagnostic only.

The current `85ff83c` portable package was replayed against all 44 rows in the
sealed `evals/wrench-expanded-v2/final.jsonl` slice. The teacher capture was
the previously recorded 44-row capture from the same input hash. No provider
call, training, LoRA update, expert selection, or prompt tuning used this
rerun.

## Receipt summary

- 44/44 traces completed, including 24 eligible mechanical rows.
- Wrench weighted final success: `1.0`.
- Wrench weighted verifier success: `1.0`.
- Weighted frontier-token coverage: `1.0`.
- Net frontier-token savings: `1.0`.
- Wrench frontier tokens: `0`.
- Wrench local tokens: `4,805`.
- Wrench p50/p95 latency: `200.154 / 316.626 ms`.
- Prohibited accepts: `0`.
- Unexpected mutations: `0`.
- Paired final-success difference 95% CI: `[0.0, 0.113636]`.

Primary receipts:

- `evaluation.json`
- `trace-manifest.json`

## Boundary

This confirms current-head regression on the sealed diagnostic slice. The suite
is still pending human approval and does not establish final family-disjoint
production approval, learned MiniMax parity, dense-native 4M decoder quality,
independent RTX 5060 Ti verification, or production enablement.
