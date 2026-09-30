# Iteration 012: installed OpenRouter mapper probe

Date: 2026-09-27 (America/Edmonton)

Status: **NO-PROVIDER PARAMETER MAPPING PROBE COMPLETE; NORMAL CONTROL PATH DROPS PRICE/PIN FIELDS; PUBLIC PROXY NOT CALLED**

## Scope

Use the installed LiteLLM 1.103.0 package in the already-running SubRoute
container to determine whether ordinary OpenRouter provider controls or an
`extra_body.provider` envelope survive LiteLLM's normal parameter mapping.
This was a local request-construction probe only. It made no HTTP call to
SubRoute, OpenRouter, or a model, and did not read credentials or change
configuration.

The exact adapter source was
`/app/.venv/lib/python3.13/site-packages/litellm/llms/openrouter/chat/transformation.py`.
Its `map_openai_params` method maps general parameters, extracts only
OpenRouter `transforms`, `models`, and `route` into `extra_body`, then assigns
that object to the mapped parameters (lines 57-82). `transform_request` merges
the resulting `extra_body` into a constructed request (lines 147-172).

## Probe and result

Using a synthetic message and `model="minimax/minimax-m3"`, call the installed
adapter's `map_openai_params(..., drop_params=True)` followed by
`transform_request(...)` for each of these input forms:

1. Top-level parameter `provider={max_price, only, allow_fallbacks}`.
2. `optional_params.extra_body={provider={max_price, only, allow_fallbacks}}`.

Both constructed request bodies were:

```json
{"messages":[{"content":"synthetic probe","role":"user"}],"model":"minimax/minimax-m3","usage":{"include":true}}
```

Neither request contained `provider`, `max_price`, `only`, `allow_fallbacks`,
or an `extra_body` object. The adapter's normal parameter mapping therefore
drops both attempted control forms when `drop_params=True`. This is a stronger
result than source-only uncertainty for the adapter layer, but it is not a
public-proxy end-to-end capture. It does not rule out a different LiteLLM
proxy path that injects `extra_body` after mapping; that path must be
demonstrated before relying on it.

A read-only `GET /openapi.json` on port 4000 succeeded. The published
`/v1/chat/completions` request schema requires `model` and `messages`, and its
properties do not include `provider` or `extra_body`. This describes the
documented request contract; the route handler reads the raw request body, so
the OpenAPI schema alone does not prove how it handles unknown JSON fields.
No POST was sent to the public route.

## Public-route source trace

The installed LiteLLM 1.103.0 source closes most of that gap without making a
request. `proxy_server.py:10984-11015` reads the raw chat-completion body and
hands it to common request processing. `common_request_processing.py:2418`
calls `route_request(data=self.data, route_type="acompletion", ...)`.
`route_llm_request.py:425-536` then routes that same dictionary to
`llm_router.acompletion(**data)`. SubRoute's `dynamic_router.py:238-275`
resolves the model and adds routing metadata; it does not inject `provider` or
`extra_body` controls.

The ordinary public route therefore reaches the OpenRouter adapter's normal
parameter mapping tested above. With `drop_params=True`, neither the top-level
controls nor `extra_body.provider` are present in the constructed upstream
body. This is a source-traced conclusion supported by the adapter probe, not
an HTTP capture from `/v1/chat/completions`; the public route was not invoked.

## Consequences

- Do not use `provider.max_price` or `provider.only` supplied as ordinary
  request parameters as spend or provider-pinning controls on this route.
- Do not treat a request's configured MiniMax model price as a hard upstream
  cap. OpenRouter documents `max_price` as a price filter that blocks a
  request when no matching provider is available, but the installed adapter's
  normal mapping removed the control fields. [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)
- The public `/v1/chat/completions` route was not called because its force-mode
  target is a paid OpenRouter model and no numeric aggregate cap was supplied.
  Per-generation selected-provider and billed-cost receipts are also still
  unverified. No spend occurred.
- The live candidate fit remains blocked by RAM: 15.39% free versus its 25%
  start requirement. No model training or inference occurred.

Next useful route work is to patch or extend the gateway adapter under an
isolated, local mock-upstream test, then prove its forwarded body and response
receipt without changing the active SubRoute configuration. Only after those
controls are preserved should Wrench's live caller implement reservation-based
cap enforcement.

The adapter source shows `transform_response` adds a hidden cost parameter from
OpenRouter's response usage when available, but this probe did not verify that
the public proxy exposes it to clients or whether it preserves a provider
identity and generation ID.

## Job accounting

Local job: `WRENCH-GATEWAY-SUBROUTE-ADAPTER-PROBE-20260927-01`.
Storage admission before the documentation write was `WITHIN_LIMIT` at
10,955,723,703 actual bytes plus 6,103,000 active reservation bytes. A fresh
100,000-byte reservation covered this report and final checks under
`WRENCH-GATEWAY-SUBROUTE-ADAPTER-PROBE-20260927-01`; it was released after
output accounting. This was not a delegated job and produced no model/provider
artifact.

The public-route source-trace addition and goal update used a separate fresh
100,000-byte reservation, `WRENCH-GATEWAY-SUBROUTE-PUBLIC-PATH-TRACE-20260927-01`,
created after a new status check and released after final accounting. No
model/provider artifact was produced.
