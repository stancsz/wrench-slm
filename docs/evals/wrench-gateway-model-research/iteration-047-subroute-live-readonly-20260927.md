# Iteration 047: SubRoute live read-only verification (2026-09-27)

## Scope

The owner directed use of the existing SubRoute setup on port 4000. This check
used read-only HTTP GETs against `127.0.0.1:4000`; it made no completion POST,
did not read credentials, and did not change gateway configuration.

## Observed route

All four GETs returned HTTP 200: `/health/liveliness`, `/models`, `/model/info`,
and `/api/active-model`. The live snapshot reported:

| Field | Value |
| --- | --- |
| Active alias | `openrouter` |
| Active mode | `force` |
| Policy version | `4` |
| LiteLLM model mapping | `openrouter/minimax/minimax-m3` |
| Advertised input / output | 1,048,576 / 512,000 tokens |
| Advertised input / output price | $0.30 / $1.20 per million tokens |
| Function calling / tool choice flags | `true` / `true` |

These fields confirm that the requested local route is reachable and identify
its configured model mapping. They do not prove which upstream endpoint serves
a generation, that a request's provider controls reach OpenRouter, that a tool
call succeeds, or what a billed response would be.

The Wrench caller source points to
`http://127.0.0.1:4000/v1/chat/completions`, requests alias `openrouter`,
restricts provider to `minimax`, disables provider fallbacks, and supplies
per-token rate ceilings. The existing callback-level mock does not demonstrate
the live HTTP-to-LiteLLM-to-OpenRouter control path. That path remains an
unverified integration boundary pending an authorized, capped experiment.

## Spend gate

The Wrench caller has a durable local ledger that reserves its approved
worst-case campaign exposure before dispatch and retains ambiguous calls. This
is not evidence of a separate limit on the OpenRouter credential configured
inside SubRoute. OpenRouter documents `provider.max_price` as a per-million-token
price ceiling; it is not a campaign-wide dollar limit. OpenRouter separately
documents API-key spending limits, with requests rejected after the key reaches
its configured limit. A dedicated experiment key limit is the provider-side
cap to pair with the Wrench ledger if the SubRoute can be configured to use
that key.

Sources: [OpenRouter API-key creation and spending-limit fields](https://openrouter.ai/docs/api/api-reference/api-keys/create-keys),
[OpenRouter provider price ceilings](https://openrouter.ai/blog/tutorials/how-to-get-the-lowest-cost-llm-inference-on-openrouter/).

No numeric aggregate USD cap or key-level limit has been provided or verified,
so generation remains closed. The `force` mode and alias mapping alone do not
authorize a paid request. There is no provider, generation, usage, or bill
receipt from this iteration.

## Resource and storage admission

At the start of the check, Windows reported 2,894.4 MiB free of 32,701.8 MiB
(8.85% RAM). The RTX 5060 Ti reported 15,219 MiB free of 16,311 MiB and 1%
utilization. RAM is below Wrench's 10% minimum, so no model workload was
admitted. The storage checker included the SubRoute repository and reported
`WITHIN_LIMIT` before this documentation reservation. This report used a
50,000-byte reservation; release it after final file accounting.

## Disposition

The requested SubRoute is live for read-only inspection and its configured
frontier alias is now pinned in the current evidence. This does not change any
model recommendation or establish Wrench effectiveness, local completion,
95/5 routing, token or dollar savings, coding quality, or all-day reliability.

No tests, inference, training, benchmark, provider request, or credential read
was performed.
