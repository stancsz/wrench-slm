# E0 pilot edge-case fixture evaluation

Job: `W2-NS-PILOT-EDGECASE-FIXTURE-20260925`

Nonce: `PILOTEDGE-5A23`

Artifact: `tests/fixtures/e0_pilot_edge_cases_v1/manifest.json`

Canonical manifest SHA-256:
`63d21349dc1c4e1075618f37642f281149d9d6538400659d82ab8e842d693016`

## Scope and verification

The new open-development-only manifest, detached hash, focused route test, and
task report are under review. The existing admitted v2 manifest and its source
pin are outside the change. Focused verification used the cached Windows
Python 3.11 runtime and passed **9 tests**. `git diff --check` reported no
whitespace errors; Git emitted only line-ending notices for unrelated dirty
files.

## Independent review

Review 1 (`W2-NS-PILOT-EDGECASE-REVIEW-20260925`, nonce `PILOTREV-8E11`)
returned **NEEDS_CHANGES**. It found the test compared the detached sidecar
with a digest computed from the same mutable manifest but did not pin an
expected digest in test source. The test now pins
`63d21349dc1c4e1075618f37642f281149d9d6538400659d82ab8e842d693016` and
checks both the sidecar and recomputed canonical digest against it. The updated
focused suite passed **9 tests**. Fresh independent review 2
(`W2-NS-PILOT-EDGECASE-REVIEW2-20260925`, nonce `PILOTREV2-246A`) returned
**PASS** at observed HEAD `0123979281170440162972d7163510dbfdb3e1ff`. It verified
the source-pinned manifest identity, inline hashes, supported route mechanics,
experience-record rejection, and report scope. The reviewer made no edits and
ran no tests. HEAD had advanced from the declared base because other parallel
work committed; the reviewer inspected only these untracked fixture files.

## Limits

This fixture is synthetic regression material only. It provides no evidence of
LLM prompt-injection resistance, semantic localization, actual tool selection,
large-hot-region handling, customer coverage, or utility. It is explicitly
excluded from experience-record and training use.
