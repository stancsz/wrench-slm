# Phase 432: Bound weighted coverage to a workload universe

Date: 2026-09-22

## Finding

`tools/score_mechanical_worker.py` previously divided successful Wrench
mechanical-workload token mass by the teacher token mass of only the traces
present in the replay. If a replay omitted most eligible work, its observed
subset could still score 100% coverage. The active Gate D requires at least
90% of the weighted mechanical-workload frontier-token mass, so the denominator
must include the authorized eligible workload universe, including cases that
did not appear in the matched replay.

## Correction

The scorer accepts an optional `eligible_workload_universe` with a schema,
source identity, source scope, and unique case IDs with weights and teacher
frontier-token counts. It checks each observed eligible trace against that
declaration and counts missing universe cases in the coverage denominator.
Only verified successful, non-fallback, safe eligible traces contribute to
covered mass. Malformed, duplicate, non-finite, mismatched, or zero-mass
universe data fails closed.

Without a universe, the old subset result is retained only as
`diagnostic_observed_subset_coverage`; active weighted coverage is null, its
gate is false, and the status is `INCONCLUSIVE_WORKLOAD_UNIVERSE_MISSING`
unless another diagnostic gate already fails. With a declared universe, the
coverage threshold can be evaluated, but this scorer still cannot issue an
active Gate D pass: it lacks verified local and fallback overhead and paid-cost
reconciliation. Net savings remains null and a coverage-positive result is
`INCONCLUSIVE_NET_UTILITY_UNVERIFIED`. Human review of the universe source is
required; its hash and scope fields alone do not establish completeness.
Historical receipts were not rewritten.

## Verification

- Focused tests show one observed case out of ten equal-mass universe cases
  scores 10%, not 100%; nine score 90% but do not pass net utility. A weight
  mismatch fails closed. Existing observed-subset and safety tests remain.
  The full repository suite passes 291/291 with 18 existing deprecation
  warnings.
- [The read-only rescore](historical-v83-rescore.json) of the saved Phase 205
  44-case diagnostic returned exit code 1 and
  `INCONCLUSIVE_WORKLOAD_UNIVERSE_MISSING`. Its historical receipt said
  `PASS_MECHANICAL_WORKER` and 100% coverage; the new receipt preserves 100%
  only as observed-subset diagnostic, with active coverage and net savings null.
- No provider request, new workload capture, promotion, or release decision
  occurred. Gates C and D remain open.
