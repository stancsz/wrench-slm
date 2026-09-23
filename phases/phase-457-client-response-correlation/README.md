# Phase 457: bind client responses to exact requests

Date: 2026-09-23

## Change

The local client computes SHA-256 over the exact serialized HTTP request body
for each attempt. The model-local server hashes the bytes it actually reads
and echoes that digest in its Wrench receipt. The client now requires a
nonempty request ID, matching workflow ID, exact attempt number, matching
body hash, and matching model identity before parsing or verifying the
proposal. A mismatch returns `qwen_response_correlation_invalid` or
`qwen_response_identity_invalid`; it does not expose a file observation or
attribute response cost to the workflow.

Each retry hashes its newly serialized body independently. Existing canonical
message hashes continue to describe retrieved model input; the new receipt
hash identifies the full HTTP body sent by the client.

## Verification

- `python -m pytest tests/test_context_client.py tests/test_wrench_server.py -q`:
  26 passed in 16.73 seconds after the final hardening changes.
- The client regression injects wrong workflow ID, attempt, empty or duplicate
  request ID, HTTP-header request ID, nested cost request ID, body hash, and
  model identity while returning a valid read proposal and complete-looking
  usage. Each mismatch abstains before proposal execution and records zero
  attributed attempts. Server coverage checks exact body hashing and rejects a
  short HTTP body before JSON parsing. Duplicate receipt IDs cannot inflate
  the distinct accounted-attempt count.
- The local server regression checks that its receipt hash equals SHA-256 of
  the exact bytes submitted and that workflow and attempt identity are echoed.
- `python -m ruff check src/wrench_harness/client.py
  src/wrench_harness/server.py tests/test_context_client.py
  tests/test_wrench_server.py`: passed. `git diff --check`: passed, with only
  Git line-ending conversion warnings for existing working-tree files.
- Independent three-tier code review has been dispatched; its report is not
  included in these test results.

## Limits

This proves local request/response binding mechanics for the covered paths.
It does not prove behavior through every named external client, cancellation
or timeout recovery, correct task outcomes, teacher parity, net savings, or
Gate D production utility. No model inference, provider call, external
benchmark, or real-workflow replay was run.
