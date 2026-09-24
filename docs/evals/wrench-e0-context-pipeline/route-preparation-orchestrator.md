# Evaluation: E0 route-to-preparation orchestrator

Job: `W2-NS-E0-ROUTE-PREP-ORCHESTRATOR-20260925`
Nonce: `E0RP-IMPL-39F2`
Baseline: `d054e4a67024a5c828f114529a458f090964266f`
Observed HEAD: `958c7e351cc6c45707f5eb0d500a4ee94eae7f1d`
Independent reviewer: `/root/route_safety_audit/route_preparation_composition_review`.
Review job: `W2-NS-E0-ROUTE-PREP-ORCHESTRATOR-REVIEW-20260925`;
nonce: `E0RP-REV-510D`; result: **PASS**.

## Result

`route_and_prepare_e0_context` runs the route itself and refuses to call
preparation unless the returned route is complete and has bounded, unique,
successful exact-read evidence. It derives every preparation path from that
evidence and marks those paths required and preserved. The receipt binds
snapshot, route status/action/counters, per-path route and preparation hashes,
the preparation hash, and the verified preparation-accounting digest.

Five authored synthetic cases passed when invoked directly under the existing
offline Python 3.11.16 interpreter: successful hash join, route abstention,
stale-snapshot rejection, required-evidence budget omission, and bounded
receipt digest/mutation rejection. The standard pytest command could not run
because neither existing Python 3.11 nor Python 3.13 has the `pytest` module;
no package install was attempted. This was an incomplete environment search,
not a test failure. A follow-up found the already-cached pytest package and
reran the actual suite successfully, as recorded below.

## Pytest re-verification

At HEAD `958c7e351cc6c45707f5eb0d500a4ee94eae7f1d`, the exact focused suite
passed using Python 3.11.16 and the approved existing cached pytest package:

```powershell
$env:PYTHONPATH = 'C:\wrench-slm-data\cache\wrench-v2-test-deps-20260923\site-packages;src'
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp C:\wrench-slm-data\cache\W2-NS-E0-ROUTE-PREP-PYTEST-REVERIFY-20260925\pytest-tmp tests/test_e0_route_preparation.py
```

```text
.....                                                                    [100%]
5 passed in 1.42s
```

No package was installed. The source and test SHA-256 values were respectively
`010f64a70b5df7dbaff85cc50dc6f13785b91ef1d3b2acb4eddcbd636b1acc81` and
`af27ad812a8b52c31a44c227ec4099629f464652ba3925943a7b9b62351b7b76`. The
10,000,000-byte reservation was released, the 8,540-byte test scratch tree
removed, and post-cleanup storage returned `WITHIN_LIMIT`. Full storage and
resource details are in the [worker report](../../reports/wrench-e0-context-pipeline/route-preparation-orchestrator.md).

## Limits

This is local structural evidence for a code-owned composition path. It does
not authenticate the caller or route execution and proves no user intent,
consent, client-hook provenance, dispatch/veto, final provider prompt or
tokenizer parity, downstream latency, provider/tool/retry/auxiliary calls,
usage/cost, task truth, or customer utility. It does not close complete E0
accounting or E0 acceptance. Independent source review passed. The reviewer did
not run tests; the separately recorded focused pytest run passed. The review
did not dynamically exercise the inter-step filesystem race. This remains a
bounded local slice, not full E0 acceptance.
