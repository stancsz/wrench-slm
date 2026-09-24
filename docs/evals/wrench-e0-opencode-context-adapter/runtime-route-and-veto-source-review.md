# OpenCode route and hook-failure source review

Date: 2026-09-24
Revision: `82a5f341defa88192a41856d3f67ebf203908c29`
Status: source-path finding accepted; installed-runtime behavior remains open

## Scope

Reviewed the isolated OpenCode `v2.0.15` configuration, read-only loopback
model-list responses, the Wrench request-lowering and session-root
reports, and the tagged OpenCode `v2.0.15` Promise adapter, hook dispatcher,
model-request preparer, session hook types, and primary runner. Two independent
read-only subagent audits also checked the hook failure path, configured
serializer/tokenizer boundary, and endpoint-identity limits.

## Findings

- The installed config selects `wrench-local/current` using OpenCode's
  OpenAI-compatible Chat Completions provider at
  `http://127.0.0.1:4000/v1`. The Wrench Responses / GPT-4.1 source pin is a
  separate research candidate and does not describe this config.
- A read-only `GET /v1/models` on the local gateway returned HTTP 200. The
  `current` model-list row included `owned_by: openai`; the response also
  advertised several other aliases. Read-only inspection of the container's
  mounted config showed `current` maps to `openai/current`, but active state
  was `mode: force`, `active_model: openrouter`, `policy_version: 4`. The
  mounted routing callback is configured, and its source rewrites requests to
  the active model in force mode. The `openrouter` alias maps to
  `openrouter/minimax/minimax-m3`. Under the mounted state, the configured
  upstream alias would be MiniMax M3, but an environment override can change
  which active-state file the running router uses. This is not an observed
  generation route or an immutable model revision. The listener is the
  `unified-llm-gateway` container, not a standalone OpenCode inference
  process. No credential value was inspected or emitted.
- In the pinned source, the Promise adapter passes the awaited `session`
  callback through `Effect.promise`; the core hook trigger yields each
  callback result and returns only after they complete. `SessionModelRequest`
  runs the context hook while preparing the request. The primary runner then
  yields `context.request.primary` before calling `steps.attempt`. A rejected
  `session.context` callback therefore prevents that **primary request
  attempt** from reaching the downstream step in the tagged source.
- The hook API has no typed deny/admission result. Compaction, title, and
  generation flows use separate hook kinds. The source trace does not verify
  failure UX, session settlement, scheduler retries, all auxiliary requests,
  or the installed executable's behavior. This is not a production-qualified
  dispatch gate.
- The selected serializer target for later characterization is the pinned
  OpenCode `v2.0.15` OpenAI-compatible Chat Completions lowering path. No
  tokenizer is pinned for the configured MiniMax M3 alias; exact prompt-token
  parity remains gated. Do not substitute `o200k_base` from the separate
  GPT-4.1 Responses candidate. The gateway's forced route policy is mutable
  and must be frozen and bound into any future run.

Primary source links: [Promise plugin adapter](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/plugin/src/promise/adapter.ts),
[core hook dispatcher](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/plugin/hooks.ts),
[request preparation](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/session/model-request.ts),
[session hook types](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/plugin/src/effect/session.ts),
and [primary runner](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/core/src/session/runner/llm.ts). The local router behavior was verified in [dynamic_router.py](<C:\Users\stanc\github\subroute\src\unified_llm_gateway\plugins\dynamic_router.py:218>) and its allowlisted model mapping in `C:\Users\stanc\github\subroute\config\litellm.yaml` (safe parsed fields only).

## Verification and limits

The primary source files were read at the `v2.0.15` tag (commit `6f3639d`,
per the existing source pin). The worktree was at the revision above before
these documentation edits, with only the preexisting `uv.lock` untracked.
Two read-only loopback `GET /v1/models` checks were performed for this review;
no client was launched, no prompt or provider POST was sent, and no inference,
test, benchmark, install, or external-provider request occurred. The model
listing plus mounted policy/source inspection establish the configured route
only. They do not prove a generation request's final destination or no-spend
behavior.

The next technical action is to identify whether already available,
non-secret gateway metadata pins an immutable model/revision and matching
tokenizer, and to establish which active-state path the running gateway uses.
If those are unavailable, leave runtime parity gated. A later plugin
integration must also cover auxiliary request kinds or clearly scope its gate
to the primary request only, and characterize failure UX and retry/settlement
behavior before any runtime use.
