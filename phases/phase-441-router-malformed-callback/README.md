# Phase 441: malformed ProposalRouter callback results fail closed

Date: 2026-09-22

## Scope

This phase hardens result validation only at the existing opt-in, test-only,
loopback `ProposalRouter` callback boundary. It does not change the ordinary
server route, model worker, provider integration, persistence, or production
routing. It makes no provider/model calls and does not run another soak.

## Finding and repair

A deterministic regression reproduced a malformed callback result with
`status: "successful"` being returned as if it were a router outcome. An
`abstain` result with no non-empty `fallback_reason` was also not canonical.
The regression failed before the repair because the response retained the
unknown `successful` status.

The test-only server boundary now normalizes a non-object result, an unknown
status, or an abstention without a non-empty reason to
`status: "abstain"` and `fallback_reason: "router_worker_result_invalid"`.
The router observes this as a failed invocation, applies its existing circuit
policy, and subsequent requests are rejected while the circuit is open. The
parameterized regression verifies canonical output, circuit transition,
bounded child launch, and child cleanup for the malformed cases.

## Verification

- The two malformed-result regression cases pass; before the repair, the
  unknown-status case failed with `successful` escaping the handler.
- `py -3 -m pytest tests/test_gate_e_serving_path.py tests/test_router_state.py tests/test_wrench_server.py -q`: 43 passed in 25.76 seconds.
- Full current-worktree suite after the repair, `py -3 -m pytest -q`: 341 passed with 18 existing Windows asyncio deprecation warnings in 47.52 seconds.
- `ruff check src/wrench_harness/server.py tests/test_gate_e_serving_path.py`: passed.
- Q4 contract validation: `VALID`.
- Focused-test preflight: 55.1% free system RAM and 14,569 MiB free of 16,303 MiB GPU memory. Full-suite preflight and in-run checks stayed at 54.6% and 54.1% free RAM, with 14,551 MiB and 14,571 MiB free GPU memory, respectively.
- No provider request, model completion, or soak was run.

## Limits and release status

This verifies malformed callback handling in the test-only serving fixture.
It does not exercise the real model worker, server-process restart recovery,
production routing, complete accounting, sustained operation, or the paired
utility thresholds. Gate E remains open, and this phase does not change the
production NO-GO status. The separate Phase 440 decision about test-only
server-process state persistence remains unresolved.

## Rollback

If this regression causes a failure, revert only the malformed-result
normalization and its dedicated regression cases. Preserve the previously
approved test-only serving integration and all pre-existing working-tree
changes and receipts. No changes were staged or committed for this phase.

## Source identities at handoff

These are whole working-tree source hashes at phase documentation time; the
files also contain pre-existing changes outside this phase.

- `src/wrench_harness/server.py`: SHA-256
  `7B932C8CD205A6B925DF01BA1EC1278CC63D091B055CC74060C6AD32A06515A8`
- `tests/test_gate_e_serving_path.py`: SHA-256
  `BF08C86C755D746F13094B7F0B0366BB957DD7F91914A05024A62ADC5C889C93`
