# Iteration 075: LiteLLM 1.101.0 source-level adapter compatibility

Date: 2026-09-28 (America/Edmonton)

## Versioned source check

SubRoute's `uv.lock` pins `litellm==1.101.0`. The official tagged
`OpenrouterConfig.transform_request` in LiteLLM 1.101.0 has the six-parameter
signature checked by `openrouter_request_controls.py`: `self`, `model`,
`messages`, `optional_params`, `litellm_params`, and `headers`. It removes
`extra_body` from optional parameters and merges its entries into the returned
request dictionary. The same tagged `custom_httpx` handler serializes the
transformed dictionary using `json.dumps(data)` before the HTTP post.

Sources:

- [LiteLLM v1.101.0 OpenRouter transform](https://github.com/BerriAI/litellm/blob/v1.101.0/litellm/llms/openrouter/chat/transformation.py#L134-L158)
- [LiteLLM v1.101.0 custom HTTP handler](https://github.com/BerriAI/litellm/blob/v1.101.0/litellm/llms/custom_httpx/llm_http_handler.py#L297-L323)
- Local pinned dependency: `C:\Users\stanc\github\subroute\uv.lock`, LiteLLM package entry at line 1252.
- Local adapter: `C:\Users\stanc\github\subroute\src\unified_llm_gateway\plugins\openrouter_request_controls.py`.

The pinned source matches the wrapper's signature guard and direct serialized
request path. This is useful source-level compatibility evidence, not an
exact-version runtime regression pass. Iteration 073's passing controls and
ASGI mock ran with LiteLLM 1.103.0. No test was run against 1.101.0.

## Current execution gates

Fresh free RAM was 3,074.5 / 32,701.8 MiB (9.40%), below the 10% resource
floor. Free VRAM was 15,200 / 16,311 MiB on the RTX 5060 Ti. No test, model,
or gateway runtime request was started after that sample. The live
`unified-llm-gateway` container on port 4000 predates the current config and
request-controls plugin edits; its process-loaded controls remain unverified.

The storage checker reported `WITHIN_LIMIT` with SubRoute included at
10,994,140,944 actual bytes before a 20,000-byte report reservation. C: had
144,944,050,176 bytes free. No completion, provider request, or credential read
occurred. The numeric campaign spend cap remains unspecified. The 95% local
completion, 5% frontier routing, retained task success, 95% frontier-token and
all-in cost reductions, and all-day engineering remain unproven.
