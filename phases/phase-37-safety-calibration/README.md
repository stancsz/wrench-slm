# Phase 37: safety-focused tier calibration

The prior strict unseen comparison found prohibited boundary accepts in both
packed tiers. The existing training split contained only four boundary rows,
all for the same delete-repository prompt. This phase adds all eight distinct
boundary cases from the explicit evaluation fixture, repeated ten times, to
the original 200-row training set. Both the 8E and 16E BF16 candidates were
retrained and repacked.

Calibration lineage:

- Dataset: `D:\models\wrench-calibration-v7-safety\train.jsonl`
- Dataset SHA-256: `c4f5f8f275cf45b4255827984aafb80c278aa93107fd8756d8a1d437b51c0e4f`
- 280 rows, 500 steps, rank 8, alpha 16, learning rate `5e-4`, seed 17
- Final loss: `0.42584192752838135`
- Source: `D:\models\Wrench-Qwen3.6-8expert-profiled-BF16-calibrated-v6`

The resulting W4A16 NVFP4 text-only artifact is
`D:\models\Wrench-Qwen3.6-8expert-profiled-W4A16-NVFP4-calibrated-v7-Safety-ExplicitSchema-TextOnly-HF`.
It is 3,423,498,186 bytes, or 3.188 GiB, with the same 3,881,244,016
parameter structure as the prior 8E tier.

On the same 28-case unseen fixture through the strict local adapter:

- 8/20 task cases were accepted, unchanged from the prior 8E pack.
- 0/8 boundary cases were accepted; all eight abstained.
- Expected accept-or-abstain outcomes matched 16/28.

On the independent 14-case holdout, the safety-calibrated 8E pack accepted
4/9 task cases, abstained on all 5 expected-abstention cases, and matched 9/14
expected outcomes. This confirms the boundary improvement on a separate split,
while also showing that task acceptance remains too low for a quality claim.

This is a safety improvement receipt, not a production quality claim. Matched
real-workflow value and human approval remain open.

The parallel 16E safety artifact is
`D:\models\Wrench-Qwen3.6-16expert-profiled-W4A16-NVFP4-calibrated-v4-Safety-ExplicitSchema-TextOnly-HF`,
at 3,991,755,191 bytes, or 3.718 GiB. It produced 6/20 accepted task cases,
0/8 prohibited boundary accepts, and 14/28 expected outcome matches. The
prior 16E pack produced 8/20 accepted task cases and one prohibited boundary
accept, so this safety candidate is recorded but not promoted as the larger
default until the task-regression tradeoff is resolved.
