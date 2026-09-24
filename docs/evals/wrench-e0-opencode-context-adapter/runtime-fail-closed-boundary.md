# OpenCode runtime fail-closed boundary readiness

Reviewed revision: `8f551ea5d1e69bda794fa943f38384973f5b2bbd`
Date: 2026-09-24
Reviewers: `opencode_hook_path_supervisor` and `e0_acceptance_gap_supervisor`,
with their independent read-only worker audits.

## Finding

The bounded Python preparation and materialization seams have historical
fixture and code-review evidence, but no OpenCode plugin is installed or
registered. The isolated OpenCode v2.0.15 profile is statically configured for
`http://127.0.0.1:4000/v1`; the corrected config has not been loaded by the
client. No client request was made during these audits.

The tagged OpenCode source connects its context callback to primary model
request preparation before `LLM.request`. The callback API has no typed veto
result and does not document failure settlement or retry semantics. A rejected
callback stops the source-traced primary attempt before its `llm.stream` call,
but this does not prove durable dispatch denial or user-visible runtime
behavior. The context event also precedes provider serialization, so it cannot
establish final wire or tokenizer parity.

Existing Wrench checks accept caller-supplied event, preparation join, and
transition evidence. They do not authenticate that OpenCode invoked them or
prevent the caller from ignoring a rejection. Lifecycle receipts do not
observe actual dispatch, provider usage, tools, retries, or task outcomes.

## Recommendation

The next source increment should be a project-local OpenCode v2 plugin using a
fixed, bounded request/response bridge to the existing Python preparation
engine. The plugin should preserve the event on success, apply only the
compiler-bound context insertion, and reject the callback on every missing,
invalid, stale, over-budget, timeout, or bridge error result. The bridge must
obtain project root and policy from explicit Wrench-owned configuration, not
from arbitrary callback fields. It must use a fixed executable and module with
`shell=false`, strict input/output byte limits, minimal environment, and no
payload logging. This is a source-level rejection contract, not yet a runtime
dispatch guarantee.

Before loading or running that plugin against OpenCode, a separate bounded
runtime experiment needs process-level egress confinement and explicit
authorization. The existing [mock runtime preflight](../../reports/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md)
still forbids launching the OpenCode client until confinement is demonstrated
and separately approved. Never direct that experiment to port 4000; the local
gateway route is mapped to an external model provider.

If a confined runtime test cannot establish that rejected preparation settles
the request without downstream model or tool work, the client integration
needs a Wrench-owned dispatch boundary rather than a context-hook-only claim.
The proxy option would change the configured client route and requires a
separate product decision before implementation.

## Evidence limits

This was source and repository review only. No tests or scripts, OpenCode
client, plugin, provider, endpoint, prompt, repository snapshot, or model were
used. Reviewers inspected the exact pinned v2.0.15 plugin/context hook, plugin
loader, discovery, hook trigger, request preparation, and runner source, plus
the current Wrench preparation and lifecycle code. This evaluation does not
establish runtime configuration loading, process isolation, provider
serialization, tokenizer parity, or E0 acceptance.

Primary OpenCode references: [context hook type](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/effect/session.ts),
[plugin loader](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/plugin/module.ts),
[plugin discovery](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/config/plugin/source.ts),
[hook trigger](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/plugin/hooks.ts),
[request preparation](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/model-request.ts),
and [LLM runner](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/core/src/session/runner/llm.ts).
