# Iteration 013: SubRoute boundary decision

Date: 2026-09-27 (America/Edmonton)

Status: **LOCAL ROUTE RECHECK AND DESIGN DECISION COMPLETE; NO PATCH, PUBLIC COMPLETION POST, OR PROVIDER SPEND**

## Scope and identities

This iteration used the owner's existing SubRoute at `http://127.0.0.1:4000`.
Wrench source HEAD was `af01304824f079a64b6c3902397a2034b843511a`. SubRoute
source HEAD was `51d262370b3de790ee97ec6b9d43c33e4b44a2ee`; its existing
untracked `.gitattributes` was preserved. The live container image was pinned
to `sha256:bd07ceb1fc7c4505f116c4eb2767956a8accba3119548dd8ae55e5356a381d56`.
The deployed LiteLLM package is 1.103.0, while the SubRoute host project pins
1.101.0. The deployed OpenRouter transformation file hash was
`8a7936d6dcca86bcddda9ac18d7cb6aaf76d98fc1bb73652f6abef659fa926f7`.

A local `GET /v1/models` returned 19 aliases and included `openrouter`. The
read-only active model state is `openrouter`, mode `force`, policy version 4.
The checked-in route maps that alias to
`openrouter/minimax/minimax-m3`. The GET and configuration do not identify the
provider selected for a generation or provide a billed-cost receipt.

## Installed mapper probe

In the running container, a pure call to `OpenrouterConfig.map_openai_params`
used these synthetic fields: `max_price`, `provider.only`,
`allow_fallbacks`, and `extra_body.probe`. It returned `{'extra_body': {}}`.
The same ordinary fields passed to `OpenAIGPTConfig.map_openai_params` returned
an empty mapping; its supported parameter list does not include OpenRouter's
provider-selection or price fields. These are local parameter-mapping probes,
not HTTP requests. They supplement the more complete `drop_params=True` plus
`transform_request` result in [iteration 012](iteration-012-openrouter-mapper-probe-20260927.md).
The generic OpenAI probe does not establish that a complete OpenAI-compatible
request with a separately supplied `extra_body` will preserve those fields.

No source or active configuration in SubRoute was changed. No public proxy
completion request, provider request, credential, or generation receipt was
used.

The LiteLLM `/utils/transform_request` endpoint was not used. Although the
[LiteLLM docs](https://docs.litellm.ai/docs/) describe it as a request
transformation debugging tool, the installed 1.103.0 implementation in
`proxy/proxy_server.py:13135-13153` calls `litellm.utils.return_raw_request`.
The installed `litellm/utils.py:9950-9977` then invokes the selected LiteLLM
completion endpoint with `api_key="my-fake-api-key"` to force a failure. That
can attempt an outbound provider request; it is not a local-only serializer.
An upstream [LiteLLM issue](https://github.com/BerriAI/litellm/issues/33952)
also reports provider I/O and event-loop blocking in this endpoint. We did not
POST to it on the active force-routed configuration.

## Advice consultation and decision

The local `codex-sol-advisor` service on port 4040 answered this question:
which boundary should own a minimal fix that preserves provider and cost
controls and yields per-generation receipts? It recommended a narrow adapter
at the SubRoute-to-upstream boundary after provider-specific mapping. The
model-rewrite hook runs too early to preserve controls removed by LiteLLM's
mapper. Its proposed falsification test uses an isolated mock upstream and
checks both the outbound request and the resulting receipt.

The consultation used 488 prompt tokens and 391 completion tokens, 879 total.
`decision_changed: true`: the implementation choice is now a post-mapping
adapter with a mock-upstream regression test, rather than relying on the
existing model-rewrite hook or assuming normal parameters survive. This is a
design decision only. The adapter and test have not been implemented or
verified.

The mock must prove that `max_price`, provider pinning, and fallback policy
reach the upstream body. Its response fixture must prove the public caller can
record the requested alias, resolved model, selected provider, actual usage,
billed cost, and generation ID as separate fields. Stop before any paid arm if
the extension point is broad or version-fragile, any control is absent, or a
receipt field is unavailable. Keep the active force-mode configuration
unchanged until that local test passes. A numeric aggregate spend cap is still
unspecified, so no paid request is authorized by this iteration.

## Resource and storage record

The latest host sample during this work showed 3.48 GiB free of 31.94 GiB RAM
(10.9%) and 15,233 MiB free of 16,311 MiB VRAM. The fit 03 start gate requires
25% free RAM, so training remains blocked. No training or inference job ran.
The latest pre-finalization storage scan reported `WITHIN_LIMIT` at
10,957,838,287 actual bytes plus 6,103,000 active reserved bytes, including
the external SubRoute checkout. The initial 100,000-byte reservation under
`WRENCH-GW-SUBROUTE-SOL-CONSULT-20260927-01` covered the consultation packet
and report and was released after accounting. A second 100,000-byte reservation
under `WRENCH-GW-SUBROUTE-TRANSFORM-ENDPOINT-SOURCE-TRACE-20260927-01` covered
the source trace and report update. A third 100,000-byte reservation under
`WRENCH-GW-SUBROUTE-REPORT-FINALIZE-20260927-01` covered the final report
correction and checks. Both later reservations were released after final file
accounting.

This iteration does not demonstrate Wrench effectiveness, 95/5 routing,
frontier-token savings, all-in cost savings, coding quality, or sustained
engineering. See the [active goal](../../goal/wrench-gateway-model-research/GOAL.md)
for the remaining proof gates.
