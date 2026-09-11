# Production evidence matrix

Updated: 2026-09-11

This matrix is the completion audit for the active selective-offload goal. A
green local test does not satisfy a broader production requirement unless the
scope matches the requirement.

| Requirement | Authoritative evidence | Current state | Reason |
| --- | --- | --- | --- |
| Oracle-free local route | `tests/test_selective_offload.py`; frozen runtime hash in `selection-eligible-v2.json` | PASS | Routing is separated from offline scoring |
| Fresh held-out local correctness | `evaluation-eligible-v2/summary.json`, `rows.jsonl` | PASS, bounded | 90/600 local, 90/90 accepted precision |
| No prohibited local actions | Held-out verifier receipt and mutation fields | PASS, bounded | 0 accepted prohibited actions, 0 mutations |
| Reproducible package identity | `selection-eligible-v2.json`; `preflight-20260911/run.json` | PASS | Frozen package, policy, protocol, and data hashes match |
| Trusted production replay | `verify_trusted_readiness.py`; approved 2026-09-11 source inventory | FAIL / unavailable | 92,431 events and 12,226 tool records still lack joinable prompt/context |
| Versioned cost ledger | Same readiness receipt | FAIL / unavailable | `PRICE_LEDGER_REQUIRED` |
| Verified production latency | Same readiness receipt | FAIL / unavailable | `DURATION_UNIT_UNVERIFIED_OR_OUTLIER` |
| Matched cloud-only baseline | M3 A/B/C receipt | NOT RUN | No authorized provider run |
| Frontier tokens saved after correction | M3 A/B/C analysis | NOT MEASURED | No provider calls in current evidence |
| Final outcomes no worse than baseline | M3 paired outcome analysis | NOT MEASURED | No matched episodes |
| Operator enable/rules-only/disable decision | M4 decision receipt | OPEN | Current safe posture is bypass or rules-only |
| Fixed gateway model-list reachability | Read-only `GET /v1/models` probe | PASS, narrow | HTTP 200; M3 model advertised; `/health` is HTTP 404 |
| Paid-run readiness enforcement | `scripts/run_authorized_selective_pilot.py`; focused wrapper tests | PASS | Current rejected receipt stops before frozen runner; passing receipt forwards |
| Captured gateway tool canary | `LIVE_CAPTURE_CANARY_20260911.md`; canary2 receipts | NO-GO | V21 abstained, saved 0 frontier tokens, added 0.834s |

## Current decision

The evidence supports a narrow local read-only capability, not production
readiness or frontier-token savings. The production-value scorecard is the
summary document: [PRODUCTION_VALUE_SCORECARD.md](PRODUCTION_VALUE_SCORECARD.md).

## Required evidence to close the open rows

The same frozen task and executor must run three arms:

1. Cloud-only baseline.
2. Rules-plus-fallback.
3. Learned-plus-fallback.

Each episode must record provider prompt, completion, cached, and billed token
fields when available, request count, retries, fallback, local and cloud time,
total latency, corrections, final outcome, and failure class. The comparison
must use family-paired uncertainty and must not promote the learned path unless
it saves frontier tokens after verification without worsening final outcomes or
violating the runtime boundary.

The runner must first pass the independent trusted-data readiness gate and must
receive explicit attempt and cloud-token ceilings plus operator authorization.
The exact intake contract is documented in
[PRODUCTION_EVIDENCE_INTAKE.md](PRODUCTION_EVIDENCE_INTAKE.md).
