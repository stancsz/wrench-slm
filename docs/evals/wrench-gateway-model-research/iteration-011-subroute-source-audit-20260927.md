# Iteration 011: SubRoute source audit and current gates

Date: 2026-09-27 (America/Edmonton)

Status: **ROUTE CONFIG CONFIRMED; TOP-LEVEL PRICE CONTROLS DROPPED; PUBLIC-PROXY ENVELOPE AND RECEIPTS UNVERIFIED; NO GENERATION; LORA FIT BLOCKED BY RAM**

## Owner direction and active route

The owner confirmed use of the existing SubRoute at
`http://127.0.0.1:4000`. The running `unified-llm-gateway` container reports
image prefix `bd07ceb1fc7c`, matching the prefix of the image digest pinned in
SubRoute's Compose file: `sha256:bd07ceb1fc7c4505f116c4eb2767956a8accba3119548dd8ae55e5356a381d56`.
The SubRoute configuration binds the `openrouter` alias to
`openrouter/minimax/minimax-m3`; the previously read-only runtime policy is
force mode, so the request's model string alone is not the final route receipt.
SubRoute's `pyproject.toml` declares LiteLLM 1.101.0, while its route config
sets `drop_params: true`. A local import inside the running container reports
LiteLLM **1.103.0**. Use the runtime package, not the host dependency file, as
the authority for adapter behavior.

The latest reply supplied no numeric aggregate USD cap. The earlier
instruction to use SubRoute at port 4000 remains the route direction, not spend
authorization. No generation, credential inspection, or SubRoute
configuration change occurred.

## Source-level audit

Read-only assignment `WRENCH-SUBROUTE-PROVIDER-PRICE-PASSTHROUGH-20260927-01`
(nonce `3ea98911-9324-4b25-aef1-d99b640705fd`) inspected the SubRoute source at
HEAD `51d262370b3de790ee97ec6b9d43c33e4b44a2ee` and
`unified-llm-gateway` at HEAD
`9fadbfdbde0232cd09727a73c0f53387154444fb`; both HEADs were unchanged after
review. The existing untracked `.gitattributes` in the SubRoute checkout was
preserved.

The OpenRouter model alias is configured in the separate checkout at
`C:\Users\stanc\github\subroute\config\litellm.yaml:37,46`. Its router hook
(`src/unified_llm_gateway/plugins/dynamic_router.py:238-275`) rewrites the
model and adds route metadata, but the reviewed project source does not
implement or prove forwarding of the nested OpenRouter fields
`provider.max_price`, `provider.only`, or `provider.allow_fallbacks`. LiteLLM
owns HTTP request parsing and provider translation. `drop_params: true`
(`config/litellm.yaml:296`) does not establish how this pinned LiteLLM version
handles these nested fields. Therefore source inspection is insufficient to
claim that OpenRouter's documented `max_price` price filter protects requests
through port 4000.

A local call to the installed OpenRouter adapter's
`OpenrouterConfig.map_openai_params` supplied those three fields as ordinary
request parameters with `drop_params=True`. It returned
`{"extra_body": {}}`: the fields were dropped at the provider-adapter mapping
boundary. This directly rules out assuming that a top-level `provider` object
will reach OpenRouter through the current adapter path. The adapter's
`transform_request` merges an explicit `extra_body` at
`/app/.venv/lib/python3.13/site-packages/litellm/llms/openrouter/chat/transformation.py:147-172`,
but whether the public SubRoute endpoint accepts and preserves that envelope
is still untested. The mapper is at the same file's lines 57-82. This probe
called no completion method and made no SubRoute API or provider request.

SubRoute sets `disable_spend_logs: true` (`config/litellm.yaml:302`). Its
provider usage display (`src/unified_llm_gateway/provider_usage.py:80-89`)
reads OpenRouter aggregate account credits, not per-generation identity or
billing. The checked-in code did not establish that a completion receipt from
this gateway exposes the selected upstream provider, OpenRouter generation
ID, and actual billed cost. Do not treat configured LiteLLM prices or
aggregate account deltas as a per-request receipt.

In the installed adapter's response transformer, an OpenRouter `usage.cost`
value is placed in a LiteLLM hidden parameter named
`llm_provider-x-litellm-response-cost`; parsing exceptions are swallowed and a
missing cost does not fail the response. This source path alone does not show
that the hidden value is returned to the public client. The code is at the
same installed adapter file's lines 175-230. The request body and headers
visible at the SubRoute boundary still need a no-spend capture.

OpenRouter documents `provider.max_price` as a filter that blocks a request
when no eligible endpoint satisfies the maximum prompt and completion rates.
That is the control we would want at the upstream boundary, but its behavior
through the current local gateway remains unverified. [OpenRouter provider
routing documentation](https://openrouter.ai/docs/guides/routing/provider-selection)

## Current resource and storage checks

| Check | Result |
|---|---|
| System RAM | 4.90 / 31.94 GiB free (15.34%); above the 10% floor but below the fit-03 25% start gate |
| GPU | RTX 5060 Ti; 15,264 / 16,311 MiB VRAM free |
| Storage before this documentation job | `WITHIN_LIMIT`; 10,955,698,217 actual bytes plus 6,103,000 active reservation bytes |
| C: free space | 155,432,955,904 bytes |
| Generation requests / provider spend | 0 / $0 |
| Adapter training / inference | None |
| Installed gateway library | LiteLLM 1.103.0; local adapter probe dropped top-level provider controls |

Fit 03 remains blocked. Do not start it until its 25% free-RAM start gate,
fresh reservation, destination headroom, and all other candidate-bound checks
pass. Do not terminate unrelated applications to force that gate.

## Required no-spend follow-up

Before any paid arm, a separate no-provider test must capture the outbound
request body produced by the pinned LiteLLM image, then test the explicit
`extra_body` envelope through the public proxy route. Confirm whether all
three provider controls reach OpenRouter unchanged. Separately establish a
response receipt for requested/resolved model, selected provider, token usage,
and billed cost. The Wrench caller must then reserve worst-case cost before
each call, stop against an explicit aggregate cap, and fail closed on missing
or conflicting receipts. The current `tools/run_diagnostic_worker_arms.py` is
still not safe for generation: it defaults the teacher alias to `minimax`
instead of this route's `openrouter`, parallelizes teacher calls, and converts
missing usage or cost to zero. Do not route it to SubRoute for live calls.

## Process notes and outcome

The source audit produced no files. No model generation or provider request
was made.

Two process deviations are recorded. First, the delegated read-only audit was
dispatched after a storage status check but before creating a fresh per-job
reservation, contrary to the repository's delegation admission rule. Second,
minor wording edits were made after the initial documentation reservation had
been released. Neither deviation created a model/provider artifact; neither is
retroactively admitted by the later reservation. The final documentation
check is covered by fresh reservation
`WRENCH-GATEWAY-SUBROUTE-FINAL-DOC-20260927-01`, created after a new status
check. Future delegated or artifact-producing jobs must have both an
immediate status check and reservation before dispatch or writes.

The gateway is confirmed as the intended read-only endpoint, but its current
configuration and direct provider-adapter mapping are not yet a verified
bounded-billing experiment route. The numeric cap and per-request receipts are
still missing. No Wrench effectiveness,
95/5 routing, frontier-token savings, all-in cost savings, or sustained
engineering result changed in this iteration.
