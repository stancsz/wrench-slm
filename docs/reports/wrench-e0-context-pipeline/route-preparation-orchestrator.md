# E0 route-to-preparation orchestrator

Job: `W2-NS-E0-ROUTE-PREP-ORCHESTRATOR-20260925`
Nonce: `E0RP-IMPL-39F2`
Worker: `/root/e0_lifecycle_audit/facade_metrics_audit`
Baseline: `d054e4a67024a5c828f114529a458f090964266f`
Verified repository HEAD: `958c7e351cc6c45707f5eb0d500a4ee94eae7f1d`
Status: accepted as a bounded local composition slice after independent source review.

## Change

Added `src/wrench_harness/e0_route_preparation.py`. Its
`route_and_prepare_e0_context` function invokes `run_e0_rule_route` internally
using a supplied root binding and snapshot. It does not accept a route result or
path list. Only a completed route with bounded, unique, successful exact-read
evidence proceeds. The function derives all preparation paths from those
evidence rows and marks each path required and preserved.

The returned canonical receipt binds the route snapshot, status, route/action,
read counters, hashed path references and route content hashes to the
preparation hash and the preparation accounting digest. Its verifier checks
bounded canonical JSON, the digest, the preparation accounting verifier, and
the route-to-preparation hash joins. Receipt validation is structural and does
not authenticate the route caller or any runtime event.

Added `tests/test_e0_route_preparation.py` for the successful three-source
hash join, route abstention, a stale snapshot, required evidence omitted under
a one-token context budget, and oversized or mutated accounting receipts.
Worker-execution and process-launch tripwires are included in the success case.

## Verification

The five authored test functions were directly invoked in the existing offline
Python 3.11.16 environment with bytecode generation disabled and temporary
fixtures under `C:\\wrench-slm-data\\cache\\W2-NS-E0-ROUTE-PREP-ORCHESTRATOR-20260925`:

```text
PASS orchestrator hash join
PASS route abstention
PASS stale snapshot
PASS budget omission
PASS bounded receipt mutation
5 passed
```

`pytest` could not start: the existing Python 3.11 and 3.13 environments both
report `No module named pytest`. No package was installed. `git diff --check`
reported no whitespace errors at the recorded HEAD; Git printed line-ending
warnings for unrelated working-tree files.

### Pytest re-verification

That initial discovery missed the approved cached pytest package. At the same
HEAD, the assigned suite was rerun using the existing Python 3.11.16 interpreter
and cached package, with no install or network access. The five tests passed:

```powershell
$env:PYTHONPATH = 'C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp C:\wrench-slm-data\cache\W2-NS-E0-ROUTE-PREP-PYTEST-REVERIFY-20260925\pytest-tmp tests/test_e0_route_preparation.py
```

```text
.....                                                                    [100%]
5 passed in 1.42s
```

The earlier direct invocation of the same five test functions also passed; it
was a separate assertion-runner check, not a substitute for this pytest run.
At HEAD `958c7e351cc6c45707f5eb0d500a4ee94eae7f1d`, SHA-256 identities were:

- `src/wrench_harness/e0_route_preparation.py`:
  `010f64a70b5df7dbaff85cc50dc6f13785b91ef1d3b2acb4eddcbd636b1acc81`
- `tests/test_e0_route_preparation.py`:
  `af27ad812a8b52c31a44c227ec4099629f464652ba3925943a7b9b62351b7b76`

The implementation run reserved 10,000,000 bytes and the later documentation
correction reserved 1,000,000 bytes; both included
`C:\\Users\\stanc\\AppData\\Local\\uv\\cache` and were released. For pytest
re-verification, storage admission was `WITHIN_LIMIT` at 10,052,620,913 actual
bytes plus 5,103,000 bytes in other active reservations, before adding the
10,000,000-byte job reservation. After pytest, actual use was 10,052,631,793
bytes with all 15,103,000 active reservation bytes counted. Its 8,540-byte
scratch tree was removed from the job-specific approved cache path. The job
reservation was released; the post-cleanup checker again returned
`WITHIN_LIMIT` with 10,052,624,501 actual bytes and the 5,103,000 other active
reservation bytes included. At the final test run, C: had 183,794,753,536 free
bytes, system RAM headroom was 41.65%, and the NVIDIA GPU reported 15,205 MiB
free of 16,311 MiB.

Independent review: job `W2-NS-E0-ROUTE-PREP-ORCHESTRATOR-REVIEW-20260925`,
nonce `E0RP-REV-510D`, returned **PASS**. The reviewer checked the internal
route invocation, route-to-preparation path/hash joins, omission behavior,
bounded receipt, and scope claims. The reviewer did not execute tests; the
pytest result above is the separate verification. The review noted that the
inter-step filesystem race is not dynamically exercised.

## Limits and next step

This only composes local deterministic route and preparation outputs over one
snapshot. It cannot authenticate user intent, consent, route execution,
OpenCode hook provenance, dispatch/veto, final provider serialization or
tokenization, downstream request timing, provider/tool activity, retries,
usage/cost, cancellation, or task outcome. The composed outcome receipt remains
incomplete. It does not satisfy the North Star complete request accounting or
E0 acceptance gates.

This bounded composition slice is accepted. Remaining E0 gates include pinned
OpenCode runtime and dispatch evidence, final request/tokenizer parity,
complete lifecycle accounting, authenticated outcome evidence, and customer
utility. No commit was made by the worker.
