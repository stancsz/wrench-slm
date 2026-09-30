# Iteration 014: post-mapping request seam and runtime gates

Date: 2026-09-27 (America/Edmonton)

Status: **POST-MAPPING SEAM CONFIRMED IN DEPLOYED SOURCE; NO IMPLEMENTATION OR MOCK TEST RUN**

## Authoritative state

Wrench HEAD remains `af01304824f079a64b6c3902397a2034b843511a`. SubRoute HEAD
remains `51d262370b3de790ee97ec6b9d43c33e4b44a2ee`; its only reported working
tree item is the pre-existing untracked `.gitattributes`. The running gateway
is still LiteLLM 1.103.0 on `127.0.0.1:4000`, force-routed to the configured
`openrouter` alias. No configuration or source file in SubRoute was changed.

The existing `wrench-hourly-token-reduction-monitor` heartbeat is `ACTIVE` at
an hourly interval. The duplicate `wrench-gateway-research` heartbeat is
`PAUSED`. No new automation was created; this preserves the one-active-hourly-
heartbeat contract.

The latest host resource sample was 3.17 GiB free of 31.94 GiB RAM (9.9%),
below the required 10% system floor. The RTX 5060 Ti had 15,243 MiB free of
16,311 MiB. Fit 03 additionally requires 25% free RAM at start. No test,
delegated job, training, inference, or packaging was started. The C: volume had
131.18 GiB free. Before this report reservation, storage was `WITHIN_LIMIT` at
10,957,855,535 actual bytes plus 6,103,000 active reserved bytes, including
the external SubRoute checkout.

## Deployed request path

Static inspection of the exact running LiteLLM 1.103.0 source confirms the
control point ordering:

1. SubRoute's `DynamicRoutingPlugin.async_pre_call_hook` in
   `src/unified_llm_gateway/plugins/dynamic_router.py:238-276` resolves the
   alias and adds metadata before LiteLLM's provider transformation. It does
   not own the serialized provider request body.
2. LiteLLM `OpenAIChatCompletion.acompletion` in
   `litellm/llms/openai/openai.py:884-949` awaits
   `provider_config.async_transform_request` at line 912. The inherited
   OpenAI transformation at `litellm/llms/openai/chat/gpt_transformation.py:514-549`
   delegates subclass behavior to `self.transform_request`.
3. The transformed dictionary is then passed to
   `make_openai_chat_completion_request` at line 947 and sent by the standard
   OpenAI SDK client. `_get_openai_client` accepts an injected `AsyncOpenAI`
   client and returns it when supplied (`openai.py:374-462`).

This confirms the advisor's suggested post-mapping seam and provides a way to
exercise the LiteLLM request path with a local `httpx.MockTransport`. It does
not yet identify a stable, documented SubRoute registration point for
overriding the built-in `OpenrouterConfig`, and it does not prove proxy-level
metadata survives into the transformation hook. A narrowly scoped adapter
must bind only to Wrench's marked request controls, fail closed on missing
fields, and be tested against the deployed package version. Do not use
`/utils/transform_request`; iteration 013 records that it invokes completion
with a fake key and may attempt provider I/O.

## Next proof step

After RAM is back above the 10% floor, build a no-network test harness around
the exact LiteLLM 1.103.0 classes. Run the SubRoute pre-call hook, carry a
marked route-control snapshot through the normal transformation, inject an
`AsyncOpenAI` client using a local mock transport, and assert the captured
outbound body preserves `max_price`, provider pinning, and fallback policy.
Then simulate the upstream response and verify requested alias, resolved
model, selected provider, provider-reported token usage, billed cost, and
generation ID are kept distinct and validated. This is a local adapter test,
not a live proxy request or paid-arm authorization. If no narrow, version-
bounded extension point can preserve these fields, stop and record the gap
instead of introducing a parallel provider transport.

The aggregate USD cap is still unspecified. No paid request was made. The
95/5 routing target, 95% token savings, success retention, all-in savings,
Wrench LoRA quality, and sustained all-day engineering remain unproven.

## Storage accounting

This report and goal update are covered by the 100,000-byte reservation
`WRENCH-GW-POSTMAP-SEAM-AUDIT-20260927-01`, which includes
`C:\Users\stanc\github\subroute`. Release it only after the report, checks,
and final storage status are accounted for.
