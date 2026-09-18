# Phase 13: frozen-portfolio boundary evaluation

This phase runs the proposed task families through the independent verifier
using a committed case manifest. It measures whether accepted and rejected
cases produce the expected status and fallback reason, including path escape,
regex-mode, external-health, and automatic-patch cases.

The manifest remains `pending_human_approval`. These are deterministic
boundary checks with no Qwen generation, so the receipt must not be presented
as proposal precision, task success, or a calibration result.
