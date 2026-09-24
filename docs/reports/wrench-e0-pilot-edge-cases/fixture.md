# Authored E0 pilot mechanics edge cases

Job: `W2-NS-PILOT-EDGECASE-FIXTURE-20260925`

Nonce: `PILOTEDGE-5A23`

Base HEAD: `5310bb502aec24fd6adf22b0add8d7a9feda1812`

Canonical manifest SHA-256:
`63d21349dc1c4e1075618f37642f281149d9d6538400659d82ab8e842d693016`

## Scope

Added a separate six-case authored-synthetic mechanics bundle in
`tests/fixtures/e0_pilot_edge_cases_v1/`. It does not modify or extend the
admitted `e0_synthetic_matched_tasks_v1` fixture or its source-pinned admission
digest. The manifest labels the bundle `open_development_test_only`, marks it
unsealed and non-final, and sets experience-record, training, and utility
eligibility to false. Each inline source and mutation has a SHA-256; the
canonical JSON manifest has a detached `manifest.sha256`.

Cases are `py-exact-near-search`, `ts-exact-near-search`,
`ts-multifile-triage-search`, `py-stale-after-snapshot`,
`py-missing-evidence`, and `ts-injection-is-data`. Repository and language
labels cover two Wrench-authored synthetic repository families and Python and
TypeScript-shaped snippets. The exact-versus-near cases search for a literal
including the opening parenthesis, so the longer preview identifier is not a
match. The triage mechanics case searches a finite snapshot for a literal in
the log, test, and source files. The stale and missing cases assert their
current route abstentions. The injection case reads only the explicitly
requested notes file, checks the evidence path and one exact read attempt, and
installs process/code-execution tripwires during the route call.

The fixture tests current `run_e0_rule_route` behavior only. Repository labels
do not stand in for real repositories. Search semantics are literal, not
semantic symbol resolution.

## Verification

Storage status before test execution was `WITHIN_LIMIT`: 10,044,216,458 actual
bytes, 96,074,520 active reservation bytes, 10,140,290,978 projected bytes,
and 39,859,709,021 bytes of headroom. The job reservation was 20,000,000
bytes. C: had about 184 GB free. Available RAM was 13,371 MiB of 32,711 MiB;
available VRAM was 15,215 MiB of 16,311 MiB, both above the 10% reserve.
Pytest ran offline using the cached Python 3.11 environment. Its temporary
files were directed to
`C:\wrench-slm-data\tmp\w2-ns-pilot-edgecase-20260925`.

Focused command:

```powershell
& 'C:\wrench-slm-data\cache\w2-rootbind-uv\archive-v0\j_0R9gSEmCfY82Cp\Scripts\python.exe' -m pytest tests/test_e0_pilot_edge_cases.py -q -p no:cacheprovider --basetemp C:\wrench-slm-data\tmp\w2-ns-pilot-edgecase-20260925
```

Result: **9 passed**. The default Python 3.13 interpreter lacked pytest; that
attempt stopped before test collection. No client, provider, model, network,
or real data was used. Independent review 1 required a source-pinned digest;
the correction and final review are recorded below.

Independent review 1 found the test did not pin the expected canonical
manifest digest in source. The test now asserts the detached digest against a
source constant as well as recomputing it from the manifest. Fresh independent
review 2 (`W2-NS-PILOT-EDGECASE-REVIEW2-20260925`, nonce `PILOTREV2-246A`)
returned **PASS** at observed HEAD
`0123979281170440162972d7163510dbfdb3e1ff`. The review verified the source
pin and all inline hashes, supported route assertions, non-admission through
the current experience-record builder, and the stated mechanics-only limits.
The review was read-only and did not run tests.

## Limits

This bundle does not test prompt-injection resistance in an LLM, semantic
localization, actual tool choice, context compilation, customer coverage, or
utility. It does not exercise a large required hot region or budget overflow,
which remain explicit pilot mechanics gaps. It is open development regression
material and must not enter the experience-record, training, sealed evaluation,
or utility paths.
