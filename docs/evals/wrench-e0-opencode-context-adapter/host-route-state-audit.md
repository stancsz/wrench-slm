# Review: host route-state audit

**Result: PASS for the static evidence boundary.** The report distinguishes
the mounted host configuration and router source from the already-running
process's loaded in-memory route. It does not claim that the `current` alias
was observed to call OpenRouter. It also records the state-path override,
avoids secret values, and does not infer token savings or local SLM use from
configuration alone.

No runtime request or inference was made. The model revision, tokenizer, final
template, and actual request-token accounting remain unresolved.

## Follow-up evaluation, 2026-09-24

Reviewer: root orchestrator. The independent `route_endpoint_readonly_audit`
agent inspected the gateway handler and supplied its source hash; the
orchestrator independently inspected the mounted config and made one local
GET to `/api/active-model`.

**PASS for observing the in-memory active-route snapshot.** HTTP 200 returned
`openrouter` in `force` mode at policy version 4. The handler returns the
locked state snapshot and is distinct from the POST update route. Its source
enforces loopback access and checks any Origin header. The running container's
startup configuration file is mounted from the inspected host directory, has
a pre-start timestamp, and maps the OpenRouter alias to `minimax/minimax-m3`.
No credential or environment secret was read.

This evidence improves on the earlier file-only audit: the active alias is
now observed in the running gateway. It still does not establish an exact
upstream model revision, tokenizer, actual OpenCode model request, final
serialized request body, provider usage, or savings. No prompt or inference
was made. Current verified savings remain **not established**; the live
gateway state is an OpenRouter provider route, not evidence of local SLM use.
