# Phase 458: preserve context receipts on abstention

Date: 2026-09-23

## Change

After context assembly succeeds, the local Wrench client now retains the
context receipt on mechanical abstentions, native or dynamic prefill errors,
HTTP/transport and malformed-response failures, correlation or model-identity
failures, and verifier abstentions. This keeps the retrieval decision and its
session hash available to fallback and audit consumers when Wrench declines
the request.

## Verification

- `python -m pytest tests/test_context.py tests/test_context_client.py -q`:
  22 passed in 4.36 seconds.
- Client regressions cover mechanical refusal, dynamic-prefill validation
  failure, and response-correlation mismatches with retained context receipts.
- `python -m ruff check src/wrench_harness/client.py tests/test_context_client.py`:
  passed.
- `git diff --check`: passed, with Git line-ending conversion notices for
  existing modified files.

## Limits

This improves fallback auditability for the local Python client. It does not
bound the complete serialized model prompt, establish retrieval quality, prove
named-client parity, or close any production utility gate. No model inference,
provider request, real-workflow replay, or trace access was performed.
