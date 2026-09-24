# E0 OpenCode session-bound outcome finalizer

Date: 2026-09-24 (America/Edmonton)
Code commit: `09ec015` (`feat: bind OpenCode outcome to session join`)

## Change

Added `finalize_opencode_preparation_outcome(join, postrun)`. It requires an
exact `OpenCodePreparationJoin`, checks that the post-run record is a built-in
dictionary whose `session_id` equals the join's session ID, and then delegates
to the existing generic outcome finalizer. Missing, null, or mismatched session
IDs return an invalid receipt before generic finalization.

The generic finalizer and post-run schema are unchanged. This wrapper only
binds two caller-supplied values structurally. It does not prove that the
session ID came from OpenCode, that post-run claims are complete or truthful,
or that every client/provider call was measured. References remain
caller-supplied and unauthenticated.

## Verification

- Command: `python -m pytest tests/test_e0_request_record.py tests/test_opencode_context.py -q -p no:cacheprovider --basetemp C:\\wrench-slm-data\\tmp\\pytest-opencode-session-receipt-20260924`
- Runtime: Windows Python 3.11.16 with the cached pytest dependency path.
- Result: **24 passed in 1.87s**.
- Fixtures cover successful binding plus null and mismatched session IDs.
- `git diff --check` passed before commit. The exact test scratch directory was
  removed after the run and the 20 MB reservation was released.
- Storage remained `WITHIN_LIMIT`; actual usage was approximately 614 MB.
- The final combined OpenCode context, E0 context-pipeline, and request-record
  verification passed **34 tests in 2.70s**; see the [admission-check report](admission-check.md).

## Limits

This is not full request-lifecycle accounting, measurement authentication,
client integration, provider usage capture, tokenizer parity, task-outcome
verification, or production evidence. OpenCode remains uninstalled and unrun.
