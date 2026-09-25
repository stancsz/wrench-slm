# Deterministic local operation screen 01 review

Date: 2026-09-25. Reviewed protocol/run revision: `e907878`.

## Finding

**INVALID: expected-value normalization defect.** Static review verified that
the four read-file cases returned the expected route/executor statuses and
actions, but all four were marked observation-mismatched. The synthetic
manifest's expected `read_file` observation omits its byte count. The E0 route
and core executor return that count, and the existing fixture test correctly
adds the UTF-8 source length to the expected observation before comparison.
The protocol-01 measurement runner failed to apply this same rule.

The two literal-search cases and three exact abstention cases passed their
available checks. Those partial successes are preserved in the receipt, but
there is no all-cases class pass and the read observation comparison is
invalid. Do not use these counts as an estimate of task acceptance.

## Provenance and correction

The saved receipt hash matches the report. The receipt identifies committed
HEAD `e907878`, so the failed result is reproducible at the recorded source
revision. The first runner did not hash itself in the receipt. Follow-up
protocol 02 adds its exact source hash, derives read byte counts from the
hash-verified synthetic fixture bytes, checks the isolated tree inventory,
and reports five matched pairs separately.

Reviewer: `measurement_harness_critic`, read-only static review. No code,
fixture, or output was edited by the reviewer; no execution or tests were run.
The follow-up remains limited to the already admitted exposed open-development
fixture and does not create utility or SLM evidence.
