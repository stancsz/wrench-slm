# Synthetic source-oracle conformance

Job: `W2-NS-ORACLE-CONFORMANCE-20260924`

Nonce: `ORCC-51D0`

Base HEAD: `c1342ef7d3a0f47fb1a98a6ff6cc035ba163e91a`

Worker: `/root/e4_oracle_recommendation/oracle_conformance_tests`, job
`W2-NS-ORACLE-CONFORMANCE-TESTS-20260924`, nonce `ORCCT-05A7`.

## Scope

Added `test_declared_pair_boundaries_match_source_oracle_consequences` to
`tests/test_e0_synthetic_matched_tasks.py`. It uses the existing pinned
Wrench-authored synthetic seed without changing its manifest or hash. The test
links each of the five declared pair boundaries to its source-derived result:
function symbol, log error type, literal-selected path, missing-versus-stale
mechanics reason (while retaining an unknown factual answer), and ambiguous
versus-specific configuration outcome. It checks source evidence paths and
lines against the fixture bytes where the expected answer includes a span.

The change is synthetic open-development mechanics evidence only. It does not
authenticate runtime execution or adjudicate final task success, establish
customer utility, or admit training evidence. The manifest remains bound to
its existing SHA-256:
`871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`.

## Verification and review

The default Python 3.13 interpreter did not have pytest:

```text
C:\Users\stanc\AppData\Local\Programs\Python\Python313\python.exe: No module named pytest
```

An existing approved cached Python 3.11.16 environment had pytest available.
The focused command ran there with the same module and arguments:

```powershell
& 'C:\wrench-slm-data\cache\w2-rootbind-uv\archive-v0\j_0R9gSEmCfY82Cp\Scripts\python.exe' -m pytest -q tests/test_e0_synthetic_matched_tasks.py
```

Exact output:

```text
........                                                                 [100%]
8 passed in 1.37s
```

The worker ran `git diff --check -- tests/test_e0_synthetic_matched_tasks.py`
and the supervisor ran `git diff --check` over the test, report, and evaluation:
both exited 0, with only Git's LF-to-CRLF warning for the test file. No
dependency was installed.

Reviewer: `/root/e4_oracle_recommendation` (supervisor review), **PASS**.
Static inspection confirmed all five pair branches, source evidence
references, and preservation of `unknown` for missing, stale, and ambiguous
cases. The focused suite passed. The addition does not change the fixture,
production source, or training/utility admission metadata.

Storage was `WITHIN_LIMIT` after the focused run: 2,286,777,093 bytes actual
plus 30,103,000 bytes reserved; projected 2,316,880,093 bytes with
47,683,119,906 bytes headroom. RAM/VRAM were above the required 10% reserve
before the run.

See the matching [evaluation](../../evals/wrench-e0-synthetic-matched-tasks/oracle-conformance.md).

## Limits and next action

These are source-oracle consistency assertions over ten authored synthetic
cases. They are not evidence of real workflow outcomes, prompt-injection
resistance, client/runtime dispatch, complete E0 accounting, E4 utility, or
training readiness. Keep the synthetic seed excluded from utility aggregates.

Re-run the exact focused pytest command if the source, fixture, or environment
changes; no dependency installation was needed.
