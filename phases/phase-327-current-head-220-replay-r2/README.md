# Phase 327: Current-head 220-case replay

Status: `PASS_MECHANICAL_WORKER`

This phase replays all 220 rows from the current `evals/wrench-expanded-v2/cases.jsonl` fixture against the portable package materialized from the pushed current-head candidate `85ff83c`. It uses the complete current 220-case MiniMax teacher capture from phase 296 and an explicit allowlisted health fixture.

Command:

```powershell
python tools/run_package_220_replay.py `
  --package-dir D:\models\_wrench-release-candidate-85ff83c `
  --cases evals\wrench-expanded-v2\cases.jsonl `
  --teacher-traces phases\phase-296-remote-current-220-replay-input\teacher-current-220.json `
  --root C:\Users\stanc\github\portfolio\wrench-slm `
  --output-dir phases\phase-327-current-head-220-replay-r2 `
  --health-fixture
```

## Receipt summary

- 220/220 traces completed.
- 120 traces are in the eligible mechanical category.
- Wrench weighted final success: `1.0`.
- Wrench weighted verifier success: `1.0`.
- Weighted mechanical frontier-token coverage: `1.0`.
- Net frontier-token savings: `1.0`.
- Wrench frontier tokens: `0`.
- Wrench local tokens: `24,141`.
- Wrench p50/p95 latency: `187.685 / 306.466 ms`.
- Prohibited accepts: `0`.
- Unexpected mutations: `0`.
- Teacher weighted final success: `0.8934`.
- Paired final-success difference 95% CI: `[0.0636, 0.1409]`.

Primary receipts:

- `evaluation.json`
- `trace-manifest.json`

## Boundary

This is a historical 220-case diagnostic workflow fixture, not the approved family-disjoint final evaluation. Its strict success is fixture-oracle success after independent verification. It does not prove learned MiniMax parity, dense-native 4M attention quality, independent RTX 5060 Ti verification, or production enablement.
