# Wrench-SLM production value scorecard

Updated: 2026-09-11

## Decision

**NO-GO for a production token-saving claim.** The current evidence proves a
narrow local capability and a safe runtime boundary. It does not prove that
Wrench-SLM saves frontier-model tokens in a complete workflow, because no
matched cloud-only, rules-plus-fallback, and learned-plus-fallback run has been
authorized or completed.

This is an evidence decision, not a judgment that the model has no value.

The first captured live-gateway tool canary is documented in
[LIVE_CAPTURE_CANARY_20260911.md](LIVE_CAPTURE_CANARY_20260911.md). It produced
zero frontier-token savings because V21 correctly abstained.

## Hard observed metrics

The authoritative held-out local receipt is
`artifacts/selective-offload-real-runtime-v2/evaluation-eligible-v2/`.

| Metric | Observed result | What it proves |
| --- | ---: | --- |
| Held-out requests | 600 across 120 disjoint families | Fresh bounded evaluation |
| Local results | 90 / 600, 15.00% | Narrow selective coverage |
| Offline-correct local results | 90 / 600, 15.00% | Correctness on this authored holdout |
| Accepted local precision | 90 / 90, 100% | No accepted local errors in this receipt |
| Accepted prohibited actions | 0 | No prohibited action accepted in this receipt |
| Unexpected fixture mutations | 0 | No observed mutation in this receipt |
| Unnecessary fallbacks | 0 | No measured false fallback in this receipt |
| Local latency | p50 1.39s, p95 2.77s | Local inference/runtime timing for this run |
| Exploratory family-bootstrap interval | 9.17% to 21.67% useful coverage | Uncertainty over authored families |
| Provider calls for M3 | 0 | No frontier-token savings measured |
| Frontier tokens saved | **Not measured** | Cannot support a savings claim |
| Net cost change | **Not measured** | No approved price ledger or matched run |
| Complete-workflow outcome delta | **Not measured** | No A/B/C episode comparison |

The full active-source regression suite also passed: **210 tests passed, 1
warning**. This verifies repository behavior, not production traffic.

The supported local slice is currently only `config` and bounded `lines` reads:
50/50 config requests and 40/50 lines requests returned locally and were
offline-correct. The other evaluated categories returned zero local results.
These are authored scenarios, not a prevalence estimate for production traffic.

## Production-readiness gate

The independent readiness gate was run against
`artifacts/trusted-scenarios/production-readiness-20260910-v5/receipt.json`.
It returned `REJECTED` with exit code 1 for:

- `DURATION_UNIT_UNVERIFIED_OR_OUTLIER`
- `MISSING_PROMPT_OR_CONTEXT`
- `PRICE_LEDGER_REQUIRED`
- `REPLAY_NOT_READY`

The source inventory contains usage metadata, but not the authorized prompt and
context needed to replay Wrench decisions. It therefore cannot establish
traffic prevalence, route-level savings, or end-to-end outcomes.

After operator approval, a fresh read-only inventory on 2026-09-11 recorded
92,431 event records and 12,226 completed tool records across 12 files, with
zero read errors. The receipt is
`artifacts/trusted-scenarios/source-discovery-20260911-approved/source-discovery.json`.
It again found request IDs and provider token metadata but no prompt or context
fields. A schema-only inspection of `consultations.sqlite3` found 24 valid
message arrays containing 30 messages, but no request, trace, prompt, or context
keys that can join those messages to provider usage. No message content was
printed or copied. The approved sources therefore remain insufficient for a
trusted semantic replay.

A fresh zero-provider preflight completed on 2026-09-11 and is recorded at
`artifacts/selective-offload-real-runtime-v2/preflight-20260911/run.json`.
It verified the frozen identity for all 600 evaluation tasks with explicit
budgets of 1 attempt and 1 cloud token, made no model or provider call, and
reported `preflight_complete`. This is a safety and reproducibility receipt,
not an A/B/C result.

The fixed gateway was probed read-only on 2026-09-11. `GET
http://127.0.0.1:4000/v1/models` returned HTTP 200 and advertised
`minimax/minimax-m3`; `GET /health` returned HTTP 404. This confirms model-list
reachability only. It does not confirm completion availability, billing, or
production health because no completion request was sent.

## What is verified today

- The runtime route is oracle-free and has no access to fixture gold or expected
  answers during routing.
- The accepted local operation is a bounded, read-only `read_file` shape.
- Writes, invalid proposals, timeouts, tool errors, malformed observations,
  verifier failures, and boundary-changing cases have explicit fallback tests.
- The focused safety/readiness suite passes 20 tests.
- The package identity and held-out evaluation are recorded in frozen receipts.
- The paid-run wrapper independently rejects the current readiness receipt and
  does not start the frozen runner; its rejection and forwarding tests pass
  (11 focused readiness/wrapper tests total).

## What would be required to change the decision

1. Supply an authorized, deterministically redacted prompt/context replay with
   provenance and a frozen manifest.
2. Supply a versioned provider price ledger and verified duration units.
3. Run the frozen matched A/B/C experiment: cloud-only, rules-plus-fallback,
   and learned-plus-fallback.
4. Record provider calls, input/output/cached/billed tokens, retries, fallbacks,
   local time, cloud time, total latency, corrections, final outcome, and
   failure class for every episode.
5. Promote only if learned-plus-fallback saves frontier tokens after all
   corrections and verification, with no worse final outcomes and no local
   safety violation. Otherwise keep rules-only or disable the local path.

## Reproduction

```powershell
py -3 -X utf8 scripts/verify_trusted_readiness.py `
  --receipt artifacts/trusted-scenarios/production-readiness-20260910-v5/receipt.json

py -3 -X utf8 -m pytest -q `
  tests/test_selective_offload.py `
  tests/test_verify_trusted_readiness.py `
  tests/test_build_production_readiness_receipt.py
```

Expected results on 2026-09-11: readiness `REJECTED` with the four reasons
above, `20 passed` for the focused test command, and `210 passed` for the full
active-source test suite excluding the archived duplicate test tree.
