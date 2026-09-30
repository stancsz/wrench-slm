# Iteration 227: require one upstream model identity in paired usage

Date: 2026-09-30 (America/Edmonton)
Job ID: `WRENCH-ITER227-UPSTREAM-MODEL-PAIRING-AUDIT-20260930-01`
Scope: static source audit only. No SubRoute/provider request, credential read, model run, or route change.

## Finding

`src/wrench_harness/frontier_usage.py` captures a `response_model` for each usage receipt, but `aggregate_paired_frontier_usage()` checks only that every receipt has the same `provider_route` string. It does not require the response model identity to remain the same across baseline and Wrench arms.

If an OpenAI-compatible alias preserves the same route label while selecting a different upstream model for some requests, this reducer can produce a paired token-reduction percentage across unlike models. That percentage may still describe the received token counts, but it cannot support a same-model paired quality or cost comparison. This is a latent accounting risk, not an observed SubRoute behavior. No provider calls were made to investigate route selection.

The receipt already retains `response_model`, so the missing check can be deterministic and offline. Before this reducer supports an acceptance claim, it should reject mixed response-model identities across the complete paired dataset, or require an explicit per-pair model identity contract and compute separate groups. The strict single-model option best matches the frozen same-model paired acceptance protocol.

## Cost evidence boundary

`FrontierUsageReceipt` sets `response_usage_is_billing_verified` to `False`. It counts response-reported input/output and cached input tokens; it does not establish provider billing. The separate SubRoute budget guard pins a configured provider and upstream model and uses response-reported cost for its reserve settlement. That remains a response receipt, not an independent invoice or account-ledger reconciliation. Keep all-in cost unproven until a future, separately authorized study reconciles actual charges and cache pricing for every call.

## Remediation gate

1. Add a source-level invariant that rejects more than one `response_model` across a paired aggregation, with a regression case that mixes models under one route label. Preserve the receipt identities in the error record.
2. Keep token reduction, verified success retention, cache usage and audited billing as separate outputs. Do not convert cached token counts into savings without a pinned price schedule and verified cache billing.
3. Before any real Frontier arm, require explicit numeric aggregate spend authorization and a caller-side hard cap. The current heartbeat forbids calls and SubRoute changes; this report grants neither.

## Exact inspected identities

- `src/wrench_harness/frontier_usage.py`: `3E7642CA7141F0A1B3AC0B5EF54B62E00D070BA4A6289FC4992AB8624F17D374`
- `tests/test_frontier_usage.py`: `51E38A75A7C780713ADA69EEACE4F38A1FCADEA6F2DE8F5DA916348FF12D2C33`
- `tools/subroute_budget_guard.py`: `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B`

This was a static audit. No implementation was changed and no test was run. The finding does not change the active gateway goal hash. The on-disk gateway goal SHA-256 remains `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`, which does not match the heartbeat-declared `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`.
