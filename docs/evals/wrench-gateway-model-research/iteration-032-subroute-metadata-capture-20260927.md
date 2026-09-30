# Iteration 032: SubRoute metadata capture preparation (2026-09-27)

## Question

Can the existing SubRoute at `127.0.0.1:4000` expose enough provider identity
for a bounded Wrench comparison, while preserving the Wrench-specific provider
restriction?

## Changes and checks

SubRoute's untracked `openrouter_request_controls` adapter now adds
`X-OpenRouter-Metadata: enabled` only when the request includes the validated
Wrench provider-control marker. It rejects duplicate or conflicting values;
unmarked traffic retains the prior header behavior. The provider restrictions
continue to flow through LiteLLM's OpenRouter mapping into the final SDK request
body. The corresponding no-network test was adjusted to retain the mocked
`httpx.Request`, then inspect both its JSON body and headers.

The source and test files parse successfully with Python's AST parser. A
containerized test invocation did not execute the suite: the pinned image's
default `litellm` entrypoint interpreted `python -m unittest ...` as LiteLLM
CLI arguments and exited with `No such option: -s`. No test passed as a result.
The test was not retried. The container had no network and no credential
mounts. No request was sent through the running gateway.

The source is bind-mounted read-only into the gateway container. The running
service was not restarted, so the new header behavior is not active in the
currently loaded process. No `docker compose` configuration, active route,
provider credential, or server state was changed.

| File | SHA-256 |
| --- | --- |
| SubRoute `src/unified_llm_gateway/plugins/openrouter_request_controls.py` | `334901565986DACF7E689E37AC6DA914D02BFB374732A85A09BF55FDC9F4B46E` |
| SubRoute `tests/test_openrouter_request_controls.py` | `56474AEF1CCEB773AFDD1CB2A4D065C4C67D22B94E102E71A6B66A8B0461D1E9` |

The SubRoute checkout already had owner-modified files and the adapter/test
were untracked. Those states remain intact. Only the adapter and its test were
edited in this iteration.

## What this does and does not establish

The `X-OpenRouter-Metadata` response feature is documented by OpenRouter as an
opt-in that can report endpoint provider identity. It has not been shown to
survive an inbound request through this SubRoute/LiteLLM deployment, nor has a
response's selected endpoint, token usage, or bill been captured here. The
mocked SDK boundary is not public-proxy or live-provider evidence.

The configured `openrouter` alias and MiniMax M3 rates are in the prior
[iteration 031 route audit](iteration-031-subroute-4000-route-audit-20260927.md).
The OpenRouter documentation lists `provider`, `model`, and `selected` in
response endpoint metadata when enabled, and generation metadata can report
provider, token counts, and total cost:
[Chat Completions](https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion),
[Generation metadata](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation).

A numeric aggregate spend cap is still not present. The latest user reply
repeated the request to specify a cap and route but contained no numeric cap.
Paid calls therefore remain unauthorized. The current route's per-token
`max_price` filter is not an aggregate USD budget. A durable caller-side
pre-dispatch ledger, reconciliation path, and receipt schema also remain
necessary before a paid canary.

The latest host sample had 3,543.9/32,701.8 MiB free RAM (10.83%) and
15,212/16,311 MiB free VRAM. The storage checker reported `WITHIN_LIMIT` at
10,991,807,326 actual bytes, with existing reservations included in its
projection. The 25% RAM start gate for full-fit training remains unmet.

## Decision

Keep the route at design/protocol preparation only. Before any live request,
repair and run the isolated mock test with the correct container entrypoint,
prove the marker survives the public SubRoute request path without a provider
call, implement and review the aggregate ledger, and obtain an explicit
numeric spend cap. Then run only the capped predeclared comparison. No result
from this iteration establishes LoRA utility, 95/5 completion, 95% frontier
token reduction, 95% all-in cost reduction, or all-day engineering.
