# Phase 266: paired confidence-interval scoring

Status: scorer and regression tests passed.

The mechanical-worker scorer now reports deterministic paired 95% confidence
intervals for teacher versus Wrench final-success rates. The point estimate is
workload-weighted; uncertainty is computed by resampling complete paired
traces, preserving the teacher/Wrench pairing. The scorer remains
provider-free and does not execute proposals.

## Re-scored evidence

The existing v103 trace manifests were re-scored without changing the traces:

| Manifest | Traces | Paired success difference | 95% CI |
| --- | ---: | ---: | --- |
| v103 220-case replay | 220 | `0.2065445` | `[0.1681818, 0.2818182]` |
| v103 sealed final slice | 44 | `0.2168695` | `[0.1363636, 0.3863636]` |

Both receipts remain `PASS_MECHANICAL_WORKER`. The interval is a diagnostic
uncertainty receipt, not human approval or production authorization. The
underlying 220-case suite remains historical regression evidence and the final
slice remains `DRAFT_PENDING_HUMAN_APPROVAL`.

Evidence:

- `evaluation-220.json`
- `evaluation-final44.json`
- `tools/score_mechanical_worker.py`
- `tests/test_mechanical_worker.py`

Validation: `177 passed, 18 warnings`.

