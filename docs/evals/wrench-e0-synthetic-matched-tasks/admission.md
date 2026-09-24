# Open synthetic fixture admission evaluation

Job: `W2-NS-SYNTH-ADMISSION-20260924`

Nonce: `ADMIT-9042`

Baseline: `45162350068eaf6541e15b1eec5dca995b1c0559`

## Result

The v1 fixture manifest did not contain enough state for fail-closed
classification of usage, split, sealed/final status, lineage, and review. The
v2 extension supplies those fields. The validator admits only the exact
Wrench-authored inline synthetic origin and `open_development_fixture_only`
usage, with open development split, no parent lineage, explicit non-sealed and
non-final booleans, and the existing hash-bound fixture mechanics review
receipt.

The focused suite passed **7 tests** on cached Python 3.11.16 / pytest 8.3.5.
It covers valid admission and rejection of unknown origin, missing or
disallowed usage, a requested training use, sealed/final flags, unsupported
split and lineage, invalid review state/scopes, and receipt hash mismatch. The
validator pins canonical manifest SHA-256
`871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`, compares
it with the caller-supplied sidecar digest, and recomputes it from the complete
manifest before evaluating admission metadata. A changed-content regression
checks this identity boundary. The final suite ran after this change under the
approved storage reservation. See the
[implementation report](../../reports/wrench-e0-synthetic-matched-tasks/admission.md)
for the exact test command and storage accounting.

Independent review 1, job `W2-NS-SYNTH-ADMISSION-REVIEW-20260924`, nonce
`ADMISSION-REV-9B6F`, returned **NEEDS_CHANGES** because admission metadata and
the review hash were not bound to the complete fixture manifest. The canonical
digest pin and changed-content test were added in response. A second
independent review, job `W2-NS-SYNTH-ADMISSION-REVIEW2-20260924`, nonce
`ADMISSION-REV2-67C1`, returned **PASS**. It verified the source pin, sidecar,
receipt hash, changed-content rejection, policy branch tests, and documentation
scope. Its observed HEAD was `6b23f45bb67e6e5319f0f377c8d0fc38d996b3c8`, which
had advanced from the baseline during parallel work. The reviewer inspected
the exact corrected admission files and did not run tests.

## Scope limits

This verifies metadata consistency against the one pinned locally supplied
manifest and receipt. A hash detects changed bytes only; it does not authenticate the author,
reviewer, or source of either object. The review receipt does not cover legal
rights or consent. A successful result is a development-fixture classification
and is not training-data admission, customer-data permission, a rights finding,
or E0/E4 utility evidence.
