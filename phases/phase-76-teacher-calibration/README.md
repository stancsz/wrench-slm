# Phase 76: MiniMax teacher-aligned calibration

Status: `REJECTED_DIAGNOSTIC_PROBE`

This phase captures MiniMax proposal traces from the local teacher endpoint and
derives a development-only calibration set. Only rows whose IDs begin with
`train_` are eligible for calibration. Invalid or unallowlisted teacher
outputs are rejected. The sealed or historical evaluation rows are not used
for training.

Inputs and derived artifacts:

- `teacher-calibration-224.json` preserves the raw local teacher capture.
- `train-teacher-calibrated.jsonl` contains 183 valid development rows.
- `teacher-calibration-receipt.json` records the source and derived hashes.
- `v10-server.log` and `v10-eval-profile-max32.server.log` record the local
  FreeToken serving probe.

The v10 probe used the v7 Safety BF16 Wrench checkpoint, rank-8 LoRA, alpha
16, learning rate `0.0002`, and 100 steps. The independent 220-case replay
completed with 7/220 correct outcomes, 0/120 exact eligible accepts, 19
prohibited accepts, zero transport failures, 9.873 seconds median latency,
and 11.401 seconds p95 latency. The probe is rejected and the resulting
checkpoint remains outside the release path.

The 220-case replay is diagnostic only. It is not calibration input and does
not authorize a quality claim, public publication, or learned-router enablement.
The score receipt is `v10-eval-score-220.json`. The mechanical runtime's
existing all-220 receipt remains the current bounded fast-path evidence.
