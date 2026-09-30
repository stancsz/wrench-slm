# Iteration 015: SubRoute 4000 route check and mock boundary

Date: 2026-09-27 (America/Edmonton)

Status: **READ-ONLY LIVE CHECK COMPLETE; SDK-BOUNDARY MOCK PASSES; PUBLIC PROXY, ROUTE RECEIPTS, AND SPEND-CAPPED COMPARISON NOT PROVEN**

## Scope and identities

The owner directed use of the existing SubRoute at `http://127.0.0.1:4000`.
Wrench HEAD is `af01304824f079a64b6c3902397a2034b843511a`. SubRoute HEAD is
`51d262370b3de790ee97ec6b9d43c33e4b44a2ee`; its pre-existing untracked
`.gitattributes` was preserved. The running container image is
`sha256:bd07ceb1fc7c4505f116c4eb2767956a8accba3119548dd8ae55e5356a381d56`
and runs LiteLLM 1.103.0, while the SubRoute host project pins 1.101.0.

SubRoute working-tree artifact SHA-256 identities:

| Artifact | SHA-256 |
| --- | --- |
| `src/unified_llm_gateway/plugins/openrouter_request_controls.py` | `A628AB384BEE49C5C86377A14207D543C35CA65F155ED3FFD2DC00AC16D058C2` |
| `config/litellm.yaml` | `05B40C8A4B95E7D9703DD88102F4D981F760CBF17DA30D2DEF781EF958EF0735` |
| `tests/test_openrouter_request_controls.py` | `92FD0BF7DC47FE8C1E2C027B25FB94FAE197E88267638D182D745852339AED32` |
| `tests/test_litellm_config.py` | `57863E4E2F7C3CA2988BF6F2CBB2F5C3B794C698D8229F6F343263F5211528A3` |

The user specified a provider/route but did not give a numeric aggregate USD
cap. This iteration used only read-only GET requests and local mock tests. No
completion request, provider call, training, download, or model inference ran.

## Live port 4000 snapshot

| Read-only check | Observation |
| --- | --- |
| `GET /health/liveliness` | HTTP 200 |
| `GET /models` | HTTP 200, 19 aliases |
| `GET /openapi.json` | HTTP 200 |
| `GET /api/active-model` | `active_model=openrouter`, `mode=force`, policy version 4 |
| `GET /model/info` | `openrouter` maps to `openrouter/minimax/minimax-m3`; input and output cost fields are null |

The running route does not reveal which OpenRouter provider would handle a
generation. There is no usage, billed cost, or generation ID until a real
completion receipt exists. Do not substitute a public catalog price or old
SubRoute metadata for those values. OpenRouter lists provider-dependent M3
prices on its [model page](https://openrouter.ai/minimax/minimax-m3/pricing).
Earlier research prose that called `$0.30/M` input and `$1.20/M` output
configured active rates is superseded by the current null-field live response;
those amounts were test fixture values in the mock and do not establish the
current upstream provider or aggregate spend limit.

## Provider capability and routing

OpenRouter's standard MiniMax M3 endpoint is documented without native
`tools`; its separate batch slug is a distinct route. The active SubRoute
`openrouter` model metadata was corrected to advertise `streaming`, not
`tools`. The separate SubRoute `minimax` alias targets MiniMax's native API,
whose [M3 function-calling guide](https://platform.minimax.io/docs/guides/text-m3-function-call)
shows Chat Completions tool calls. That does not change the current force
route or prove the direct alias's integration in a coding-agent loop. Any
route change needs a separately authorized and evaluated experiment.

## What the adapter test establishes

SubRoute's working tree contains a narrow callback around LiteLLM's
`OpenrouterConfig.transform_request`. It validates the marked Wrench route
controls and passes OpenRouter-only fields via the OpenAI SDK's `extra_body`
envelope. LiteLLM remains responsible for the provider transport and response
parsing. A four-test local `httpx.MockTransport` suite passed against the
deployed LiteLLM 1.103.0 package. It checks the final serialized request body,
ordinary unmarked behavior, invalid-control rejection, and conflicting-body
rejection. An initial top-level `usage` serialization attempt failed; placing
OpenRouter body fields inside `extra_body` made the SDK-boundary suite pass.

This is not a LiteLLM public proxy test. The mock bypasses the deployed proxy's
full pre-call and metadata path. The independent read-only review
`WRENCH-SUBROUTE-POSTMAP-INDEPENDENT-REVIEW-20260927-01` (nonce
`2f780cd7-9638-4505-b838-60113b91178c`) passed its assigned scope with blockers:

- the Wrench metadata marker is optional, and missing metadata falls through
  to default OpenRouter provider routing;
- the wrapper patches a private LiteLLM method and depends on an exact
  signature, while the host pin and running image versions differ;
- no proxy-level receipt verifies the requested alias, resolved model,
  selected provider, token usage, billed cost, and generation ID together.

The callback has been registered in the working-tree configuration, but the
port 4000 process was not restarted. Docker inspection showed the mounted
configuration is writable from the host and the source mount is read-only; an
earlier iteration's statement that both mounts were read-only was inaccurate.
The live process still has its old in-memory configuration. This iteration did
not restart it or change the active force route.

The `max_price` values used in the mock are per-request provider price filters,
not an aggregate USD cap. A safe paid arm still needs caller-side pre-request
worst-case reservation, a hard cumulative stop, a numeric owner-approved cap,
and fail-closed receipt validation.

## Model recommendation and evidence limits

Keep responsibilities separate:

- Deterministic Wrench code should own exact retrieval, source-linked evidence
  retention, compaction bookkeeping, path checks, and verification.
- Train a Wrench-specific LoRA for bounded context and routing proposals such
  as retrieve/stop/abstain and evidence selection. The currently inventoried
  Qwen3.5-0.8B remains the first low-cost controller candidate, not a proven
  controller.
- If frozen results show the 0.8B controller lacks capacity, evaluate
  Qwen3.5-2B as the next controller candidate. It needs its own model-tree
  inventory, adapter profile, resource preflight, and held-out evaluation.
- Treat Qwen3.5-4B or Qwen2.5-Coder-3B as separate code-worker candidates. The
  published benchmark screens do not show Wrench repository repair or
  day-long engineering. The 4B route is particularly tight against this
  host's 16 GB VRAM, and current RAM is below the training start gate.

The 128 synthetic controller examples are mechanics fixtures, not a
representative workload. They cannot demonstrate 95% local completion, 95%
token savings, 95% lower all-in cost, or sustained software engineering. A
5% frontier episode share also does not imply 5% of baseline tokens or cost.
Report paired task success/regressions, local versus frontier task share,
frontier token share, verified token receipts, full lifecycle cost, and
recovery behavior as separate outcomes. Include multiple repositories and
languages, interruption/restart cases, and repeated eight-hour sessions.

Relevant research remains bounded: [ACON](https://arxiv.org/abs/2510.00615)
reports context-token reductions on non-coding long-horizon tasks;
[OpenHands context condensation](https://www.openhands.dev/blog/openhands-context-condensensation-for-more-efficient-ai-agents)
reports a limited SWE-bench subset with comparable solve rate and lower
per-turn cost. Neither proves this system's 95/95 claim.

## Resource and storage record

The latest host sample in this task was 4,725,344 KiB free of 33,486,624 KiB
system RAM (14.1%) and 15,256 MiB free of 16,311 MiB VRAM. RAM is above the
10% runtime floor but below the fit-03 25% start gate, so no training or
inference is admitted by this snapshot.

Storage status including the external SubRoute checkout was
`WITHIN_LIMIT` after final file accounting: 10,957,906,860 actual bytes plus
6,103,000 bytes in active reservations, projected 10,964,009,860 bytes under
the 50,000,000,000-byte aggregate ceiling. This iteration's documentation,
adapter, and independent-review reservations were released after completion.
Reservations owned by other work remain active.

## Decision and next proof gate

Keep the active force route unchanged and do not send a paid request yet. To
proceed with a paid comparison, obtain a numeric aggregate USD cap and explicit
approval of the provider/route. The current `openrouter` route uses standard
M3 without native tools. The native `minimax` alias has documented M3 tool
support, but switching to it changes the experiment. Before any paid call,
prove the marker through an exact-image public-proxy test, make missing or
invalid controls fail closed, verify the per-call receipt fields, and enforce
the aggregate cap in the caller.

The storage reservation for this report and goal update is
`WRENCH-GATEWAY-SUBROUTE-REVIEW-DOCS-20260927-01`. Final storage status and
release accounting are recorded in the task closeout. The Wrench 95/5 goal,
token reduction, cost reduction, LoRA utility, and all-day engineering remain
unproven.
