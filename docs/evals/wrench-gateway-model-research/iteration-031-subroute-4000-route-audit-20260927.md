# Iteration 031: SubRoute :4000 route and spend-gate audit

Date: 2026-09-27 (America/Edmonton)

Status: **ROUTE CONFIRMED; PAID GENERATION CLOSED; NO PROVIDER REQUEST**

## Finding

The owner specified the existing SubRoute setup at `http://127.0.0.1:4000` for
the frontier comparison. Read-only GETs to `/api/active-model` and `/v1/models`
confirmed that the service is live. The active snapshot reports
`active_model=openrouter`, `mode=force`, and policy version 4. `/v1/models`
lists 19 aliases. These endpoints establish liveness and policy state, not the
provider selected for a completion or its cost.

The current SubRoute source maps the `openrouter` alias to
`openrouter/minimax/minimax-m3`. Its experimental OpenRouter callback is loaded
in the uncommitted SubRoute configuration. The callback preserves a provider
control object only when the request carries
`metadata.wrench_openrouter_provider_controls`. That marker can be absent; the
no-network regression test explicitly confirms an unmarked request keeps
default provider routing. The controls require a provider allowlist, disabled
fallbacks, and prompt/completion `max_price` values. SubRoute documents that
these prices filter a single endpoint by rate and do not impose an aggregate
USD budget. Its test exercises LiteLLM request mapping and SDK JSON with a mock
transport, not the public proxy request, a live provider, or billing receipts.

The Wrench caller is not yet admitted to this route. The diagnostic runner
rejects `:4000` for the Wrench arm before it reads the cases; its live teacher
path is separately disabled pending aggregate spend enforcement and durable
usage receipts. The local-model child also rejects `:4000` because it is not a
local Wrench model endpoint. The existing `provider_budget_guard.py` is pinned
to the direct OpenRouter HTTPS endpoint and a legacy $100 approval schema, so
it cannot safely authorize this SubRoute experiment. I made no changes to the
SubRoute checkout or active route.

## Evidence snapshot

- Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`.
- SubRoute HEAD: `51d262370b3de790ee97ec6b9d43c33e4b44a2ee`.
- SubRoute already contains owner changes in `GOAL.md`, `README.md`,
  `config/litellm.yaml`, `docs/architecture.md`, and
  `tests/test_litellm_config.py`, plus untracked provider-control source and
  tests. These changes were preserved.
- Active model GET: `openrouter`, force mode, policy version 4.
- Models GET: 19 aliases; it does not identify a future response's actual
  model/provider.
- Wrench source pins and findings:

| File | SHA-256 |
| --- | --- |
| `tools/provider_budget_guard.py` | `5D48687A5CF0CCB58C8B5D686256AD9FC2ECA713F9F36DA51D445E9BBAE21114` |
| `tools/run_diagnostic_worker_arms.py` | `91C028A6C10C921973DC4734B75D0ADD90EC4AEF15340D3F963627935336EBE1` |
| `tools/run_local_wrench_call.py` | `7B448F977A27B5A89AC4F12DCC5B4E14E9F5F5D4C473647A77F57148D8384240` |
| SubRoute `config/litellm.yaml` | `05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735` |
| SubRoute provider controls source | `A628AB384BEE49C5C86377A14207D543C35CA65F155ED3FFD2DC00AC16D058C2` |
| SubRoute provider controls test | `92FD0BF7DC47FE8C1E2C027B25FB94FAE197E88267638D182D745852339AED32` |

The live resource sample was 3,565.5/32,701.8 MiB free RAM (10.9%) and
15,228/16,311 MiB free VRAM on the RTX 5060 Ti. The fit-03 start gate requires
25% free RAM, so local full-fit work remains closed. C: had 141,296,766,976
bytes free. The Wrench storage checker admitted this report reservation under
the 50 GB aggregate limit.

### Live model-info and price cross-check

A fresh safe-field `GET /model/info` returned the active `openrouter` alias as
`openrouter/minimax/minimax-m3`, with the OpenRouter adapter, configured rates
of `$0.30/M` input and `$1.20/M` output, and model-info ID
`7ec0fcd796f4452d965d34f010bc30802a1dd926dcb39eabd474cd913172a74e`. The
separate `minimax` alias targets `minimax/MiniMax-M3` at those same rates; the
active force route is still `openrouter`. The model-info provider field names
the gateway adapter, not the inference provider selected behind OpenRouter.

OpenRouter's current [MiniMax M3 pricing page](https://openrouter.ai/minimax/minimax-m3/pricing)
shows a `$0.23/M` and `$0.96/M` headline rate, while the provider table lists
MiniMax at `$0.30/M` input and `$1.20/M` output. Other providers have different
rates. Since the SubRoute test control pins `only: ["minimax"]`, `$0.30/M` and
`$1.20/M` are the appropriate conservative rate inputs for this route, subject
to refreshing the source and verifying the returned provider before a live
study. At the legacy one-request ceiling of 256 input tokens and 128 output
tokens, the per-request reservation formula yields `$0.0002304`; this is only
a small route-canary bound, not enough evidence for effectiveness or all-day
engineering. The current forced alias is not the separately listed
`minimax/minimax-m3:free` endpoint.

## Decision and next gate

Use the owner-specified `127.0.0.1:4000` route in the experiment design, with
the current OpenRouter/MiniMax M3 mapping recorded as a configuration snapshot.
Do not send a completion request until a numeric aggregate USD cap is supplied
and a caller-side hard cap is enforced. Before the first admitted call, the
Wrench client needs a durable pre-dispatch reservation, a required provider
control marker, fixed request/output ceilings, no hidden retry or fallback,
and a durable response receipt containing the returned model, provider usage,
and cost. Unknown charge or usage must consume the entire reservation and stop
subsequent calls until reconciled. SubRoute's `max_price` is an extra route
filter, not this ledger.

After those controls exist, validate the public SubRoute path with no-network
transport tests first, then run only the owner-capped, predeclared comparison.
Keep provider response identity, actual token use, billed cost, and local
compute separate. A route-health check, synthetic comparison, or request-byte
capture is not effectiveness or savings evidence.

This iteration sent no POST, made no provider request, changed no route
configuration, and ran no tests. Wrench-specific LoRA effectiveness, 95/5
completion, 95% frontier-token reduction, 95% all-in cost reduction, and
all-day engineering remain unproven. The numeric spend cap is the only pending
owner input for the paid comparison; local work continues under its separate
storage, model, and hardware gates.
