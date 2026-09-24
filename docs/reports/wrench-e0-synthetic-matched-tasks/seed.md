# Synthetic matched-task seed bundle

Job: `W2-NS-SYNTH-MATCHED-20260924`

Nonce: `SYN-3D28`

Implementation baseline inspected: `9f5e0d57fb730552c89604bf14922e295496ed85`

## Scope

The test-only bundle at
`tests/fixtures/e0_synthetic_matched_tasks_v1/` is Wrench-authored and uses
synthetic source and log bytes only. It contains ten cases across four task
families and five matched pairs:

| Family | Pair boundary | Cases |
| --- | --- | --- |
| Localization | Exact function identifier associated with an expiry check | `loc-a`, `loc-b` |
| Failing-test/log triage | Error type in a frozen synthetic log | `triage-a`, `triage-b` |
| Context selection | Presence of an exact identifier in one snapshot source | `context-a`, `context-b` |
| Evidence availability | Requested source missing from the snapshot versus stale after capture | `evidence-missing`, `evidence-stale` |
| Evidence specificity | Vague source request versus one named path | `evidence-ambiguous`, `evidence-specific` |

Every pair declares its one changed boundary input. The focused test normalizes
that input and compares the remaining prompts, paths, and source bytes. The
manifest stores each source and post-snapshot mutation inline with a SHA-256;
`manifest.sha256` contains the SHA-256 of the canonical JSON manifest.

Canonical manifest SHA-256:

`ba64557b95f1d0948c55a7dc97ba9e48d775124bf068e53d222f343a4399ecb4`

## Oracles

Each case has two distinct checks. The mechanics expectation pins the
`run_e0_rule_route` status, action, exact observation or abstention reason, and
`route=none`. The structured-answer candidate is derived from the actual
bounded route output. A separate deterministic task oracle derives expected
fields and evidence locations from the inline synthetic source or log bytes,
then checks both the candidate and the frozen expected object. The route and
task answer oracle are test helpers; the bundle does not claim that the
production runtime answered or completed these tasks.

## Verification

The focused suite `tests/test_e0_synthetic_matched_tasks.py` passed: **4
passed** on Windows, Python 3.11.16, pytest 8.4.2. The cached pytest package
was used offline; pytest temporary files were placed under
`C:\wrench-slm-data\cache`. `git diff --check` passed. No model, provider,
client, or network was used.

Independent review job `W2-NS-SYNTH-MATCHED-REVIEW2-20260924`, nonce
`SYNREV-AC42`, returned **PASS** for the fixture scope. It verified the
canonical manifest hash, all 22 inline source/mutation hashes, answer
derivation from route results, independent source-byte outcome checks, and
the five pair normalizations. The reviewer did not run tests.

## Limits

This is an open development seed for mechanics and oracle feasibility. It is
not a sealed evaluation set, a customer or real matched-task corpus, an
estimate of real task coverage, utility evidence, or E0 acceptance. It does
not establish OpenCode prompt or tokenizer parity, dispatch enforcement,
complete request accounting, or downstream completion quality. New
repository-family holdouts and appropriately authorized real matched tasks
remain necessary before E4 utility claims.
