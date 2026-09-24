# Synthetic matched-task seed evaluation

Job: `W2-NS-SYNTH-MATCHED-20260924`

Nonce: `SYN-3D28`

Implementation baseline: `9f5e0d57fb730552c89604bf14922e295496ed85`

## Reviewed scope

The review covered the test-only fixture manifest, detached hash sidecar, and
focused test module in
`tests/fixtures/e0_synthetic_matched_tasks_v1/` and
`tests/test_e0_synthetic_matched_tasks.py`. The fixture provenance is
`wrench_authored_synthetic_only`; no user, company, public benchmark, or real
project data is present.

## Verification

Focused run on Windows, Python 3.11.16, pytest 8.4.2:

```text
tests/test_e0_synthetic_matched_tasks.py: 4 passed
```

`git diff --check` passed. The test checks the canonical manifest against its
detached SHA-256, each inline source and mutation hash, all four task families,
and the five paired cases. For every pair, it masks the declared boundary
input and requires the remaining prompt, paths, and source bytes to match.
It asserts exact mechanics results from the bounded route, derives structured
answer candidates from those results, and checks them against independent
deterministic expectations derived from the fixture source and log bytes,
including evidence paths and lines.

## Independent review

Reviewer job `W2-NS-SYNTH-MATCHED-REVIEW2-20260924`, nonce `SYNREV-AC42`,
observed HEAD `9f5e0d57fb730552c89604bf14922e295496ed85` and returned **PASS**.
The reviewer verified canonical manifest SHA-256
`ba64557b95f1d0948c55a7dc97ba9e48d775124bf068e53d222f343a4399ecb4`, matching
`manifest.sha256`, and all 22 inline source/mutation hashes. It confirmed the
source-derived answer oracle, route-derived candidate, pair invariants, exact
mechanics checks, requested coverage, and synthetic-only scope. The reviewer
did not run the test suite.

The first review returned NEEDS_CHANGES because the initial answer check was
tautological and pair isolation was only partially asserted. The final
implementation derives candidates from route results, independently derives
the expected answer from fixture bytes, and checks a generic normalization
for every declared boundary pair.

## Limits

The passing result establishes only a small synthetic fixture and deterministic
oracle regression path. It does not establish real-world task utility, model
quality, a sealed held-out result, OpenCode runtime parity, dispatch veto,
complete E0 accounting, or E0/E4 acceptance. The ten cases are an open
development seed and must not be treated as production coverage or customer
evidence.
