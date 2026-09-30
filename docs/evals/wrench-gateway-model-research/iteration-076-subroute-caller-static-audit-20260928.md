# Iteration 076: bounded SubRoute caller source audit

Date: 2026-09-28 (America/Edmonton)

## Static findings

The caller pins requests to `http://127.0.0.1:4000/v1/chat/completions`, the
`openrouter` alias, and expected upstream `minimax/minimax-m3`. The approval
loader requires a human-approved record, Wrench-authored synthetic-only cases,
matching repository/caller/case identities, zero automatic retries, disabled
fallbacks, bounded token/body/request limits, and an aggregate cap large
enough to cover every approved worst-case request reserve.

Before dispatch, `BudgetLedger.reserve` uses an immediate SQLite transaction.
It rejects any existing unresolved call, enforces campaign and job request
ceilings, adds settled spend plus outstanding reserves when checking aggregate
exposure, and commits the full request reserve before the call is marked
dispatched.

The sender makes one POST to the fixed local endpoint, disables ambient
proxies and redirects, and limits the response body to 1 MiB. The caller
requires exactly one selected OpenRouter endpoint and validates its provider
and model, generation ID, token usage and billed cost. Settlement rejects
actual cost above the reserved amount. Ambiguous or invalid results remain
unresolved and keep the full reserve.

Reviewed source identities at Wrench HEAD
`af01304824f079a64b6c3902397a2034b843511a`:

| File | SHA-256 |
|---|---|
| `tools/subroute_budget_guard.py` | `DAB8B7212E91C2687E13F53AB619E296BAE3FB91E10B716AD57EC4C4933FB00B` |
| `tools/capture_subroute_teacher_traces.py` | `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6` |

This is source review, not execution evidence. The latest caller test evidence
remains Iteration 070's 8/8 mocked cases. This review did not issue a request,
read credentials, or run tests.

## Current gates

Free RAM was 2,647.9 / 32,701.8 MiB (8.10%), below the 10% runtime/test floor.
Free VRAM was 15,197 / 16,311 MiB on the RTX 5060 Ti. C: had 144,940,871,680
bytes free. The storage checker reported `WITHIN_LIMIT` at 10,994,197,220
actual bytes with the SubRoute checkout included, before a 20,000-byte report
reservation.

No test, inference, training, benchmark, provider call, or live service restart
was made. The live port-4000 process still predates the request-controls
callback edits, and its loaded path remains unverified. The numeric campaign
cap remains unspecified. The 95% local completion, 5% frontier routing,
retained task success, 95% frontier-token and all-in cost reductions, and
all-day engineering remain unproven.
