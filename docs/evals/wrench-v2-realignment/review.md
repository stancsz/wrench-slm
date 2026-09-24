# V2 realignment review

Status: PASS for direction, repository cleanup and experiment definition

Source: working tree based on `87909b958ac252b0b3b2cc720a300babb26b733d`.
Reviewed on 2026-09-23 (America/Edmonton). This accepts the
[realignment goal](../../goal/wrench-v2-realignment/GOAL.md), not implementation
or production qualification of the full v2 runtime.

## Observed verification

| Check | Result and scope |
| --- | --- |
| Preserved inputs | Both supplied attachments copied exactly; eight earlier direction snapshots match recorded byte counts and SHA-256 hashes. |
| Model accounting | Pinned upstream metadata lists 13 files totaling 1,769,980,465 bytes. No model weight download or local model hash verification. |
| Storage ceiling | Mocked accounting accepted 49,999,999,999 bytes, rejected 50,000,000,000 and 50,000,000,001, and rejected a one-byte reservation at 49,999,999,999 used bytes. |
| Current authority | Parent monetary budget is zero with no transferred paid-canary allowance. Two focused canary tests passed, including blocking before output creation or network access. |
| Source checks | Python syntax checks passed for the changed generator/site scripts and relevant tests. `git diff --check` passed. No runtime/config implementation was changed. |
| Focused regression checks | 52 tests passed across context, toolbelt, policy, schema evaluation, patch calibration, expanded generation, router calibration and paid-cost-receipt validation. The two canary tests bring the total to 54 distinct passing tests. |
| Relocated generator paths | All 40 regenerated eligible file-read targets resolve in a fresh synthetic fixture; line bounds fit. Frozen historical evaluation rows were not rewritten. |
| Local example | `examples/local_first.py` passed its bounded read, outside-root abstention and shell abstention cases; the fixture remained unchanged. No model inference. |
| Documentation/site | Active Markdown links resolved; no loose files remain directly under docs. Site build succeeded; site checker passed 23 HTML pages, 759 local links/fragments, exact 34-file allowlist and demo receipt. No visual browser review or publication. |

The 52-test selection was `tests/test_context.py`, `test_toolbelt.py`,
`test_policy.py`, `test_schema_evaluation.py`, `test_patch_calibration_probe.py`,
`test_expanded_evaluation_generation.py`, `test_build_router_calibration_v2.py`
and `test_validate_paid_cost_receipt.py`.
The additional cases were
`test_configured_loopback_baseline_requires_exact_approved_child_contract` and
`test_zero_parent_budget_blocks_configured_baseline_before_output_or_network`
in `tests/test_paired_client_canary.py`.

## Failures encountered and repairs

- Pytest was absent. Six pinned pure-Python packages were fetched with verified
  published wheel hashes under a separate 40 MB peak reservation. Extracted
  dependencies occupy 6,179,287 bytes in the approved cache; downloaded wheel
  bytes totaled 1,709,359. The cache manifest records their identities.
- A paid-receipt test tried to mutate a tuple. Converting that test's local
  authorization fixture to a list restored its intended assertion.
- The zero-parent-budget test depended on an unavailable historical workload.
  It now creates a synthetic workload in its own temporary directory. The
  network-fails-if-called assertion and absence-of-output assertion remain.
- The first ad hoc fixture-path check supplied an already-existing directory
  to a helper that correctly refuses overwrite. The corrected check supplied
  a new child directory and passed.
- `tests/test_harness.py` could not collect because its pruning import requires
  PyTorch, which is not installed in the tested interpreter. No PyTorch or
  model packages were installed. The full repository suite was not run.

Tests used disabled third-party plugin autoloading, no pytest cache provider,
no Python bytecode writes, and unique temporary roots under the approved
Wrench cache. No surviving historical data was reconstructed for a test.

## Independent review

Read-only source/evidence audit `W2-AUDIT-20260923`, nonce
`W2-AUDIT-b3c1c9`, completed. Its [persisted findings](../../reports/wrench-v2-realignment/reuse-audit.md)
distinguish reusable v1 code, missing v2 capabilities, failure evidence and
cleanup hazards.

Fresh integrated review `W2-REVIEW-20260923`, nonce
`W2-REVIEW-86bbd4`, read both complete inputs and inspected the resulting
architecture, lifecycle, experiment, archival hashes, local links and storage
policy. It initially returned PASS_WITH_MINOR with two P3 findings:

1. The site source index still described the old scope as current. Reworded
   it to distinguish historical model-story scope from v2.
2. The storage policy needed to state that missing roots are counted as zero
   by the current checker. Added an explicit manual expected-root completeness
   obligation before admission.

The reviewer independently rechecked those exact repairs and returned PASS
with no remaining findings or missing requirements. The reviewer did not run
root's tests, render the site, verify provider-related unrelated edits, or
independently repeat external model research.

## Limits and completion decision

The measured inventoried footprint is approximately 0.59 GB, far below the
strict 50 GB ceiling. Inventory includes configured external caches and
worktrees. Missing expected roots still require manual investigation; this
checker is admission control, not a physical quota or disk-health proof.
The observed host has an RTX 5060 Ti, with more than 10% RAM and VRAM free.

The documents explicitly retain uncertainty about the incident's physical
cause, model fit, adapter composition, replay effectiveness and production
utility. E0 through E4 remain planned. No weights, learning job, paid request,
production activation, filesystem repair, commit or publication was performed.

All acceptance items for this bounded realignment are addressed. The next
product work is the E0 deterministic context/accounting baseline, followed by
the full staged Layer 1 and continual-LoRA experiment.
