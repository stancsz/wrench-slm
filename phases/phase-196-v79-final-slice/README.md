# Phase 196: v79 sealed final-slice diagnostic

Date: 2026-09-20

## Scope

This run used `evals/wrench-expanded-v2/final.jsonl`, the 44-row sealed final
slice. No final rows were added to training, LoRA calibration, expert
selection, prompt tuning, or package construction. The package was already
materialized before this diagnostic.

The v79 package-local endpoint was exercised with the client mechanical
fast-path bypassed. A deterministic loopback health fixture was enabled so
the host's unrelated `localhost:4000` service could not affect the result.

## Receipt

The runner returned `PASS_MECHANICAL_WORKER` for all 44 rows, including 24
eligible rows:

- weighted mechanical frontier-token coverage: `100%`;
- net frontier-token savings: `100%`;
- Wrench-plus-identical-fallback weighted final success: `100%`;
- teacher weighted final success: `88.9922%`;
- Wrench frontier tokens: `0` versus teacher `11,967`;
- Wrench local tokens: `4,805`;
- Wrench fallbacks: `0`;
- median / p95 end-to-end latency: `183.940 ms` / `323.980 ms`;
- prohibited accepts: `0`;
- unexpected mutations: `0`.

Raw evidence is in `evaluation.json` and `trace-manifest.json`. The input
SHA-256 is `52ed79afbef978ad8cf8a5d520ae7b9f7a608cb4a2e0b4c007f806ac1d41a331`.

## Boundary

This is a sealed-split diagnostic, not final production authorization. The
approved family-disjoint real-workflow set, paired confidence intervals,
current-commit 5060Ti verification, and operational shadow gates remain open.
The result does show that the current embedded mechanical path is not merely
passing the 220-case calibration-heavy fixture.
