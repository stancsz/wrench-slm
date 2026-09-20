# Phase 83: full 220-case workflow arms

Status: `QUALITY_GATE_OPEN`, diagnostic only.

This phase runs the complete `evals/wrench-expanded-v1/cases.jsonl` fixture,
not the earlier 28-case smoke set. It replays four arms with the same request
rows, verifier, repository root, and bounded decoding settings:

- MiniMax teacher only
- rules plus MiniMax fallback
- Wrench plus identical MiniMax fallback
- Wrench-only diagnostic

The run is recorded in `trace-manifest.json` and `evaluation.json`. The input
contains 220 historical fixture cases. It is not the approved family-disjoint
real-workflow set, and strict final success means fixture-oracle success after
the verifier, not user-confirmed task completion.

## Full-run result

| Arm | Weighted final success | Verifier success | Frontier tokens | Median latency | p95 latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| MiniMax teacher only | 49.4% | 90.3% | 93,333 | 2,177 ms | 3,193 ms |
| Rules plus fallback | 80.8% | 99.0% | 8,060 | 0.071 ms | 52.6 ms |
| Wrench plus identical fallback | 59.9% | 95.5% | 51,375 | 1,822 ms | 6,357 ms |
| Wrench-only diagnostic | 80.8% | 92.1% | 0 | 0.339 ms | 3,220 ms |

Wrench-only had zero prohibited accepts and zero unexpected mutations. Its
remaining failures were concentrated in 17 patch-draft transport failures, 10
unavailable or slow `/health` reads, one local timeout, and fixture cases whose
hidden target contains timeout or diff values not stated in the user prompt.
The rules and Wrench paths therefore demonstrate the fast mechanical boundary,
but the production gates are not passed by this receipt.

## Runner hardening

The diagnostic runner now uses killable subprocesses for teacher and non-fast
Wrench requests. Deterministic mechanical requests stay in-process. The
verifier also prunes model artifacts and bounded large files from literal
search, disables expensive untracked-file scanning for read-only Git status,
and gives health reads a total socket deadline. These changes prevent a large
local model checkout or a half-open endpoint from blocking the full 220-case
run.

## Commands

```powershell
python tools/run_diagnostic_worker_arms.py `
  --cases evals/wrench-expanded-v1/cases.jsonl `
  --root . `
  --teacher-endpoint http://127.0.0.1:4000/v1/chat/completions `
  --teacher-model minimax `
  --wrench-endpoint http://127.0.0.1:28904/v1/chat/completions `
  --wrench-model Wrench-4B-Qwen3.6-8E-Safety-Native2M-BF16 `
  --output-dir phases/phase-83-diagnostic-workflow-arms `
  --timeout 3 `
  --teacher-workers 4
```

This phase is evidence of full fixture execution and failure localization. It
does not authorize production enablement, publication of MiniMax parity, or a
95% token-saving claim.
