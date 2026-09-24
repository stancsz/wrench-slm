# Evaluation: E0 request and version scope

| Check | Result | Evidence |
|---|---|---|
| Pin is stable through activation within one request scope | Pass | `test_request_scope_keeps_starting_version_and_next_scope_sees_activation` |
| A following request scope observes activated version | Pass | Same test; synthetic lifecycle activation only |
| Explicit complete failed outcome is retained as failed | Pass | `test_complete_receipt_with_failed_task_outcome_is_bound_as_failed` |
| Incomplete terminal receipt fails closed and artifact pins release | Pass | `test_incomplete_outcome_and_exception_never_leave_request_pins` |
| Exception and absent terminal receipt leave no envelope and release pins | Pass | `test_incomplete_outcome_and_exception_never_leave_request_pins`; `test_scope_without_explicit_terminal_receipt_is_incomplete` |
| Preparer cannot close artifact pins early and still finalize | Pass | `test_preparer_cannot_close_artifact_pins_before_terminal_receipt` |
| Preparation without valid incomplete preparation receipt fails closed | Pass | `test_ready_preparation_without_matching_preparation_receipt_fails_closed` |
| Terminal snapshot mismatch fails closed | Pass | `test_terminal_receipt_with_mismatched_snapshot_fails_closed` |
| Envelope binds preparation snapshot digest explicitly | Pass | `test_request_scope_keeps_starting_version_and_next_scope_sees_activation` |
| Terminal receipt run ID must match the request scope ID | Pass | `test_terminal_receipt_from_another_request_fails_closed` |
| Focused suite | Pass | Python 3.11.16, `tests/test_e0_request_scope.py -q`, 8 passed in 5.26s |

This is synthetic structural evidence only. It says nothing about runtime/client compatibility, actual model loading, inference, outcome truth, learning utility, production activation, or persistent recovery. `production_activation=false` and `training_eligible=false` remain outside this coordinator's authority; it does not change the E3 lifecycle's development-only flags.

The first test command encountered a missing scratch-parent directory and did not execute tests. After creating the reserved scratch directory, the focused suite passed and was rerun after the early-pin-release, explicit snapshot, and request/run ID correlation checks. The exact implementation and test SHA-256 values, repository HEAD, resource admission, and remaining limitations are recorded in [`request-version-scope.md`](../../reports/wrench-e0-context-pipeline/request-version-scope.md).
