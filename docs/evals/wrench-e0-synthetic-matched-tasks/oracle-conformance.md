# Synthetic source-oracle conformance evaluation

Job: `W2-NS-ORACLE-CONFORMANCE-20260924`

Nonce: `ORCC-51D0`

Base HEAD: `c1342ef7d3a0f47fb1a98a6ff6cc035ba163e91a`

Implementation: [oracle-conformance report](../../reports/wrench-e0-synthetic-matched-tasks/oracle-conformance.md).

## Result

The scoped test addition ties the five existing synthetic pair boundaries to
source-derived oracle consequences and checks cited source lines against
fixture bytes. Static supervisor review returned **PASS** for those
assertions. The existing fixture manifest and hash were not changed.

The configured Python 3.13 interpreter did not have pytest. An already
provisioned approved Python 3.11.16 environment did; the focused command
`-m pytest -q tests/test_e0_synthetic_matched_tasks.py` passed **8 tests**.
`git diff --check` passed with only a Git LF-to-CRLF warning. No dependencies
were installed.

## Scope limits

This verifies relationships within the fixed Wrench-authored, open-development
fixture. Missing, stale, and ambiguous cases remain unknown where their
factual answer is unverifiable. The receipt does not establish task success,
route authenticity, customer utility, E0 or E4 acceptance, or training
eligibility. The seed remains mechanics-only and excluded from utility
aggregates.

No real data, model, provider, client, download, or network operation was used.
The test result remains a mechanics-only regression for this synthetic seed.
