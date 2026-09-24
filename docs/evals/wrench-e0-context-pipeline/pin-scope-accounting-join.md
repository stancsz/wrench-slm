# E0 preparation pin-scope accounting join evaluation

## Decision

Accept this as a bounded accounting improvement to the local preparation
facade. The exact closed `ArtifactRequest.pin_scope_duration_ns` value is
captured at the producer boundary, included in `PreparationMetrics`, and bound
by the canonical v2 accounting digest.

## Verification

- Implementation job: `W2-NS-E0-PIN-DURATION-JOIN-20260925`, nonce
  `PINJOIN-6D31`, based on `5310bb502aec24fd6adf22b0add8d7a9feda1812`.
- Windows Python 3.11.16, pytest 9.1.1, offline run of three named tests:
  **3 passed**.
- Test node IDs:
  `tests/test_e0_context_pipeline.py::test_exact_snapshot_to_pinned_artifact_context_schema_prompt_receipt`,
  `tests/test_e0_context_pipeline.py::test_caller_owned_source_artifact_remains_protected_after_request_close`,
  and
  `tests/test_e0_context_pipeline.py::test_facade_bounds_inputs_and_has_no_execution_surface`.
- The tests compare the metric and canonical counter against each actual
  closed scope, confirm changing the duration invalidates the saved digest,
  and preserve `null` for caller-owned scopes still open at preparation return
  and for invalid input rejected before scope entry.
- `git diff --check`: passed for the scoped source and test changes.
- Storage reservation `W2-NS-E0-PIN-DURATION-JOIN-20260925`: 30,000,000
  bytes, including `C:\Users\stanc\AppData\Local\uv\cache` and the approved
  Wrench data root for test temporary files. Final release and checker status
  are recorded by the implementation handoff.
- Independent review: `W2-NS-E0-PIN-DURATION-REVIEW-20260925`, nonce
  `PINDURREV-84B2`, returned PASS with documentation follow-ups. The v2
  validator wording, paired evaluation reference, and historical v1 label
  were repaired. A follow-up read-only review requested test node IDs and a
  completed-review result in the evaluation. Its final documentation check
  returned PASS at HEAD `0123979281170440162972d7163510dbfdb3e1ff` and
  confirmed the listed test node IDs.

## Limits

This is same-process preparation pin-scope duration. It is not task latency,
downstream request latency, OpenCode/client latency, or authenticated client
telemetry. An open caller-owned request scope remains unmeasured at the time
preparation returns. Provider usage/cost, dispatch, tools, retries, task truth,
runtime resources, consent, and complete E0 accounting remain outside this
receipt.
