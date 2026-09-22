# Phase 337: Exact current-head 220-case replay

Status: `PASS_MECHANICAL_WORKER`.

The exact current release-line package
`D:\models\_wrench-release-candidate-bbc680f` completed the full corrected
220-case diagnostic replay using the complete phase-296 MiniMax teacher capture
and the allowlisted health fixture.

## Evidence

- `220/220` traces completed, including `120` eligible mechanical traces.
- Wrench weighted final success: `1.0`.
- Wrench weighted verifier success: `1.0`.
- Weighted frontier-token coverage: `1.0`.
- Net frontier-token savings: `1.0`.
- Wrench frontier tokens: `0`; local tokens: `24,141`.
- Wrench p50/p95 latency: `190.199 / 306.474 ms`.
- Prohibited accepts: `0`; unexpected mutations: `0`.
- Paired final-success difference 95% CI: `[0.063636, 0.140909]`.

This is a current-package diagnostic replay. It validates the deterministic
mechanical-worker contract and independent verifier path, not learned MiniMax
parity, dense-native 4M attention quality, independent RTX 5060 Ti execution,
or production enablement.

Command and raw receipts are in `phase-337-current-head-220-replay/`.
