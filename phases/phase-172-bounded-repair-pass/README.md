# Phase 172: one bounded repair pass for frontier-token avoidance

Date: 2026-09-20

## Purpose

Make the high-leverage path explicit: a Wrench response that fails only local
format validation gets one cheap corrective pass before the request escalates
to the stronger model. This applies to worker and local-client paths, not only
patch prompts. Semantic safety refusals, authority failures, and verifier
failures are not retried.

## Evidence

- Full regression: `156 passed, 14 warnings in 15.38s`.
- Targeted worker, client, server, and mechanical tests: `32 passed`.
- The new worker test returns malformed JSON on pass one and a valid bounded
  `read_file` proposal on pass two.
- The result is accepted with exactly `model_calls: 2` and
  `repair_pass_count: 1`.
- The retry instruction is bounded to one pass and remains behind the same
  parser, authority, verifier, and TTC gates.

## Cost boundary

This is a local quality and escalation control, not a claim that local
inference is free. The matched workflow benchmark must charge local inference,
reducer compute, retries, corrections, and frontier fallback against the saved
frontier tokens. The intended win is to replace an expensive frontier call with
zero or one small local pass while preserving final success and safety.
