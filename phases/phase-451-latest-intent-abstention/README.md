# Phase 451: preserve latest intent and require explicit continuation

Date: 2026-09-23

## Change

The pre-assistant multi-user bundle fallback searches earlier messages only
when the newest message is an explicit continuation acknowledgment (for
example, "Please do that now."). A cancellation, correction, unrelated
request, or ambiguous message cannot revive an earlier eligible read. When
continuation is explicit, the nearest earlier user intent is considered first.

## Verification

- `python -m pytest tests/test_harness.py tests/test_embedded_worker.py -q`:
  38 passed.
- `python -m ruff check src/wrench_harness/core.py src/wrench_harness/worker.py
  tests/test_harness.py tests/test_embedded_worker.py --ignore E731`: passed.
- Plain Ruff on the two edited test files reports one existing E731 lambda in
  `tests/test_harness.py:643`, outside this change.
- Regression cases confirm earlier read intent does not override latest
  `task_family_not_allowlisted` or `action_not_allowlisted` abstentions.
- New cancellation, correction, and unrelated-request regressions confirm no
  earlier read is revived and no file content is returned.
- A separate control confirms an ambiguous latest wrapper still uses the
  earlier read intent.
- An independent source review confirmed the guard and both behavioral cases;
  its suggested second abstention reason was added before the final test run.

## Limits

This is a local intent-ordering fix. The larger audit still found that
complex-task abstention depends on a finite phrase list and an opt-in safety
gate. It does not prove overall abstention quality, independent verification
across all actions, matched teacher parity, real-workflow savings, or
operational readiness. No model inference, benchmark, provider call, or
real-workflow replay was run.
