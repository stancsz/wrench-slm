# Selective offload real-runtime V2 result

Updated: 2026-09-10

## Current verdict

The oracle-free local gate passed on fresh held-out families. The current
evidence level is **LOCAL CAPABILITY ONLY** because no matched provider A/B/C
workflow has been authorized or completed. No token-saving, cost, production,
or real-traffic claim is made.

The prior selective result is historical diagnostic evidence only. Its runtime
route used `score_answer(env.task, ...)` before returning a local result and is
not evidence for this goal. The first replacement run is also retained as
superseded development evidence because the policy import boundary changed
after that run. The v2 receipt below is the authoritative held-out run.

## Frozen identity

- Candidate: `artifacts/model-release/package-selected-v21`
- Package manifest SHA-256:
  `219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`
- Adapter SHA-256:
  `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`
- Base revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Policy: `eligible`, revision `intent-v2`
- Runtime verifier SHA-256:
  `479782e1e5a811f7f0e7870e589a20c11130267ecc9754a82b5d301d2f3c103b`
- Policy source SHA-256:
  `6d92139bcd3647c0daf14f11e83402229275b5198fe014869b6d9925940ae7d5`
- Protocol SHA-256:
  `6f540849f28261eddfe98a48ad36a61738d2874c58481fd20adcabee97a066b5`
- Data campaign: `selective-offload-real-runtime-v2`
- Data manifest SHA-256:
  `46446be692d89e81e589fd9adad0fc09a1f89ff3a6c7947de674ca2ecc05769c`
- Development split SHA-256:
  `c53e03f9ad57d244467e3d614388103d67b815485e3c2bf308b1074227cff02b`
- Evaluation split SHA-256:
  `0cda2e8873c775709ecb525def952052eeec7a54e4b1a7d760bad3f6bee64041`
- Freeze receipt:
  `artifacts/selective-offload-real-runtime-v2/selection-eligible-v2.json`
- Development receipt:
  `artifacts/selective-offload-real-runtime-v2/development-eligible-v2`

## Oracle-free runtime boundary

`wrench/selective_runtime.py` now accepts only a visible `read_file` action
with either a positive bounded line range or a public configuration-region
request. It validates the operation shape before execution. The verifier then
checks the public action, matching observation, execution status, truncation,
output shape, and unchanged boundary fingerprint.

The runtime source has no import or reference to `score_answer`, `env.task`,
`expected_answer`, fixture gold, or evaluator-only task labels. Offline scoring
is performed only after routing in `wrench/selective_eval.py` and is recorded
as `offline_correct`.

## Fresh held-out result

The evaluation assigned 600 requests in 120 disjoint families, five instances
per family, across 12 kinds and English and Chinese. Every row was routed,
including rejected and adversarial requests.

| Measure | Observed |
| --- | ---: |
| Local results returned | 90 / 600, 15.00% |
| Offline-correct local results | 90 / 600, 15.00% |
| Local accepted precision | 90 / 90, 100% |
| Accepted local errors | 0 / 90, 0% |
| Policy proposals accepted before runtime narrowing | 303 / 600, 50.50% |
| Accepted prohibited actions | 0 |
| Unexpected mutations | 0 |
| Unnecessary fallbacks | 0 |
| Local duration p50 / p95 | 1.39s / 2.77s |

The family-bootstrap receipt is:

`artifacts/selective-offload-real-runtime-v2/evaluation-eligible-v2/family-bootstrap.json`

It reports a 95% exploratory family-bootstrap interval of 9.17% to 21.67%
for both accepted and useful coverage, with 100% observed accepted precision.
Families, not individual instances, are the uncertainty unit. Authored
families are not a sample of real traffic.

## Scope slices

| Kind | Local returned / assigned | Offline-correct / assigned |
| --- | ---: | ---: |
| config | 50 / 50 | 50 / 50 |
| lines | 40 / 50 | 40 / 50 |
| search | 0 / 50 | 0 / 50 |
| git_status | 0 / 50 | 0 / 50 |
| git_log | 0 / 50 | 0 / 50 |
| health | 0 / 50 | 0 / 50 |
| draft | 0 / 50 | 0 / 50 |
| ambiguous | 0 / 50 | 0 / 50 |
| unsupported | 0 / 50 | 0 / 50 |
| missing_tool | 0 / 50 | 0 / 50 |
| invalid_range | 0 / 50 | 0 / 50 |
| over_budget | 0 / 50 | 0 / 50 |

English returned 45/300 and Chinese returned 45/300. Both language slices had
100% observed accepted precision. The supported scope is intentionally narrow.

## M1 evidence

The targeted oracle-free suite passes 29 tests. It includes a gold-free
environment with zero provider calls, operator bypass, invalid proposal,
irrelevant safe proposal, timeout, tool error, malformed observation,
insufficient region observation, verifier failure, and unexpected mutation.

The scoped repository suite passes 212 tests with the archived duplicate test
tree excluded, with one existing PEFT warning. The focused safety and
readiness subset passes 29 tests. The documented `tests` path is required
because an ignored archived export can otherwise introduce duplicate module
names during collection.

## Reproduction commands

```powershell
pytest -q tests/test_selective_offload.py

.venv\Scripts\python.exe -X utf8 scripts\selective_local_eval.py `
  --data data\pilots\selective-offload-real-runtime-v2 `
  --split evaluation `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --variant eligible `
  --revision intent-v2 `
  --output artifacts\selective-offload-real-runtime-v2\evaluation-eligible-v2
```

The evaluator records route and verifier receipts in
`artifacts/selective-offload-real-runtime-v2/evaluation-eligible-v2/rows.jsonl`;
its private gold fields are used only for post-route `offline_correct` scoring.

## Remaining M3 gap

The M3 runner preflight completed without loading the local model or making a
provider call. It verified the frozen receipt, fixed endpoint/model identity,
and all 600 assigned evaluation tasks. The preflight receipt is
`artifacts/selective-offload-real-runtime-v2/preflight-3/run.json`.

No complete matched A/B/C provider run exists for this new runtime contract.
The fixed local gateway is reachable at
`http://127.0.0.1:4000/v1/chat/completions` and advertises
`minimax/minimax-m3`, but an explicit authorized spending ceiling is still not
available. The prepared runner is
`scripts/selective_pilot_run.py`; it verifies the freeze receipt and refuses
provider calls without both an explicit token ceiling and
`--authorize-paid-run`.

The 2026-09-11 synthetic live canary and its deterministic trusted-scenario
audit are plumbing evidence only: Wrench abstained on the read request, so it
saved zero provider tokens and added 0.834 seconds before fallback. The
trusted readiness gate remains rejected for missing replayable prompt/context,
unverified duration units, missing calculated cost, and replay readiness.

Until M3 is completed, the correct operator posture is to keep the local path
limited to the verified read shape and route everything else to the stronger
model. This is not a production or release-readiness claim.
