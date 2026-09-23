# Phase 462: reject ambiguous proposal JSON

Date: 2026-09-24

## Change

The independent proposal parser now rejects duplicate JSON object keys at
every nesting level. Previously `json.loads` silently kept the last value,
which allowed ambiguous model output to reach schema and authority checks.
The parser maps duplicate-key input to the existing fail-closed
`model_output_invalid_json` abstention.

The local-client correlation fixture now returns the workflow ID, attempt,
request-body hash, request ID, and response request-ID header required by the
current client contract. This keeps the regression fixture representative of
the actual verified request path.

## Verification

- `python -m pytest tests/test_harness.py -q`: 21 passed.
- `python -m pytest tests/test_mechanical_worker.py tests/test_schema_evaluation.py -q`: 22 passed.
- `ruff check src/wrench_harness/core.py tests/test_harness.py`: passed.
- `git diff --check`: passed; Git printed existing LF-to-CRLF notices.
- Regression cases reject duplicate top-level schema keys, duplicate action
  arguments, and duplicate nested keys. Existing valid-output and
  response-correlation tests pass.

## Limits

This closes one ambiguous-JSON parsing path. It does not establish zero schema
errors across the full workload, named-client execution provenance, matched
workflow utility, or production safety. Gates A through E remain subject to
their full evidence contracts.
