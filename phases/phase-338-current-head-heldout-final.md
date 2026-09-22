# Phase 338: Exact current-head held-out final slice

Status: `PASS_MECHANICAL_WORKER`, diagnostic only.

The exact current release-line package
`D:\models\_wrench-release-candidate-bbc680f` completed the 44-row
`evals/wrench-expanded-v2/final.jsonl` slice with its matching 44-row teacher
capture.

## Evidence

- `44/44` traces completed, including `24` eligible mechanical traces.
- Wrench weighted final success: `1.0`.
- Wrench weighted verifier success: `1.0`.
- Weighted frontier-token coverage: `1.0`.
- Net frontier-token savings: `1.0`.
- Wrench frontier tokens: `0`; local tokens: `4,805`.
- Wrench p50/p95 latency: `289.126 / 353.990 ms`.
- Prohibited accepts: `0`; unexpected mutations: `0`.
- Paired final-success difference 95% CI: `[0.0, 0.113636]`.

The final slice remains diagnostic pending the repository's human and
family-disjoint approval gates. It does not prove learned MiniMax parity,
dense-native 4M attention quality, independent RTX 5060 Ti execution, or
production enablement.

Command and raw receipts are in `phase-338-current-head-heldout-final/`.
