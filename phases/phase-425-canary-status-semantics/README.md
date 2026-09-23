# Phase 425: Canary status semantics

Date: 2026-09-22

## Finding

The active productive-value contract says missing or unapproved evidence is
`INCONCLUSIVE`, never a pass. The canary runner instead labeled correct
answers with incomplete accounting as
`FAIL_PAIRED_REAL_CLIENT_HYBRID_CANARY_ACCOUNTING_INCOMPLETE`. It also treated
any nonzero hybrid model activity as `FAIL`, despite not evaluating whether
net frontier-token savings met the required threshold after local inference.

## Correction

- Missing accounting with correct baseline and hybrid answers now yields
  `INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_ACCOUNTING_INCOMPLETE`.
- Correct answers with nonzero calls but no savings-threshold result yield
  `INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_SAVINGS_THRESHOLD_UNASSESSED`.
- A known incorrect answer remains `FAIL_PAIRED_REAL_CLIENT_HYBRID_CANARY`.
- The process exit is still nonzero for every non-pass status. Only the
  scoped, fully accounted zero-call canary pass returns zero. A scoped pass is
  not `PASS_WRENCH`, does not close Gate D, and does not authorize release.
- The Phase 424 receipt remains unchanged. Its old fail label is corrected in
  interpretation, not overwritten.

Sol reviewed the status fork through the user-requested local API. Advice
usage was 347 prompt and 1,029 completion tokens, 1,376 total; the advice
changed both status mapping and regression coverage. See
[advisor receipt](advisor-receipt.json) and [consultation packet](advisor-packet.txt).

## Verification

- Focused tests: `pytest -q tests/test_paired_client_canary.py`, **25 passed**.
- Full repository suite: **273 passed**, with 18 existing deprecation warnings.
- The tests distinguish incomplete evidence, unassessed savings, genuine
  answer failure, scoped pass, and process exit behavior. Only the scoped pass
  returns exit code zero.
- Q4 contract validation returned `VALID`; compile and whitespace checks
  passed.

No provider canary, provider spend, historical receipt rewrite, release-gate
change, or production change occurred. The runner still does not compute the
full three-arm Gate D savings, weighted coverage, or Gate C confidence
intervals. Those remain open; no full-goal or release pass is claimed.
