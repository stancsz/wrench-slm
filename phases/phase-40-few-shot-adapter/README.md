# Phase 40: adaptive schema adapter prompting

The prior 16E pack's strict adapter evaluation showed serialization failures.
This phase tested runtime prompt shaping without changing the weights:

- Zero-shot calibration prompt: 8/20 task cases accepted, 1 prohibited
  boundary accept.
- One canonical accepted-read example: 14/20 task cases accepted, but 4/8
  prohibited boundary accepts.
- Accepted-read plus rejected-delete examples on every request: 10/20 task
  cases accepted and zero prohibited boundary accepts.
- Adaptive prompt policy: one accepted-read example for routine prompts and a
  second rejected-delete example for lexically risky prompts. It reached 13/20
  task cases, 0/8 prohibited boundary accepts, and 21/28 expected outcome
  matches on the same fixture.

The adaptive policy is a diagnostic candidate, not a production claim. Its
risky-prompt classifier is intentionally simple and must be evaluated on
family-disjoint real traces before any enablement decision.

