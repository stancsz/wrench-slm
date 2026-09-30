# Iteration 041: OpenCode v2.0.12 context hook and SubRoute (2026-09-27)

## Owner direction

Use the existing SubRoute at `http://127.0.0.1:4000` for the Wrench gateway
experiment. This selects the endpoint, but does not set a numeric aggregate
USD spend cap. This iteration therefore made read-only GET requests only. No
provider POST, model completion, or spend occurred.

## SubRoute check

The configured endpoint returned `I'm alive!` from
`/health/liveliness`. `/api/active-model` returned `active_model: openrouter`,
`mode: force`, and `policy_version: 4`. This confirms the local service and
forced alias are reachable. It does not identify a billed upstream deployment,
prove model compatibility, or verify tool calling.

The existing OpenCode example selects `wrench-subroute/openrouter` at
`http://127.0.0.1:4000/v1`, while leaving it out of OpenCode's default model
selection. Its synthetic HTTP hook validates a pinned synthetic body, writes a
content-free receipt, and throws before transport. This remains a safe
no-provider route check, not a live model comparison. See
[`SUBROUTE_SETUP.md`](../../../examples/opencode_v2_subroute_capture/SUBROUTE_SETUP.md).

## Verified context integration seam

Pinned OpenCode v2.0.12 source establishes a direct pre-serialization hook:

- `SessionContext` exposes `sessionID`, `model`, mutable `system`, mutable
  `messages`, mutable `options`, `agent`, and mutable `tools`.
- `SessionModelRequest.prepare` invokes the `context` hook with the draft and
  tool definitions before constructing the `LLMRequest` from the returned
  event. This is a real location to add or compact context and shape tool
  schemas before provider serialization.
- Hook callbacks return `void`; they mutate the supplied event. The hook
  registry awaits callbacks in sequence and returns that same event.
- OpenCode maps post-hook tool definitions back to real executable tools by
  object identity or original name. Invented definitions are dropped. A
  removed definition is omitted from both the advertised request and the
  executable tool set, so any learned pruning policy must preserve tools needed
  for the task and be evaluated on paired completion outcomes.
- `http.request` receives the Web `Request` immediately before transport and
  passes the hook's returned request to the transport handler. The current
  synthetic plugin uses this boundary to stop before network transport.

Primary source: [OpenCode v2.0.12 `SessionContext` and hook types](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.12/packages/plugin/src/promise/session.ts), [request preparation and hook invocation](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.12/packages/core/src/session/model-request.ts), and [hook registry semantics](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.12/packages/core/src/plugin/hooks.ts).

## Repository compatibility gap

The local context projection and E0 offline composition still identify the
hook as OpenCode `2.0.15` (`src/wrench_harness/opencode_hook_projection.py`,
`src/wrench_harness/opencode_context.py`,
`src/wrench_harness/e0_offline_request_composition.py`, and
`src/wrench_harness/prompt_compiler.py`). The installed/example target is
`2.0.12`. Although the v2.0.12 event has the same field names used by the
projection, the existing receipt version label is not evidence that the v2.0.12
runtime adapter works. Keep historical v2.0.15 receipts intact and add a
versioned v2.0.12 adapter plus source-matched fixture coverage before claiming
runtime integration.

The current E0 implementation changes messages while preserving system,
options, and tools. The v2.0.12 source confirms that a separate `session.context`
adapter can see and mutate tool schemas. This unlocks a plausible tool-schema
pruning experiment, but no such policy is implemented or measured here. The
next implementation should begin with identity-preserving pass-through plus
the existing preparation-bound message insertion; tool filtering should remain
off until an allowlist and paired retained-success evaluation are in place.

## Execution gate

At the latest local sample, free RAM was 3,295.9/32,701.8 MiB (10.08%) and GPU
free memory was 15,226/16,311 MiB. RAM is only narrowly above the 10% floor, so
no test suite, OpenCode runtime preflight, inference, training, benchmark, or
delegation ran. Storage was `WITHIN_LIMIT`: 10,990,249,442 actual bytes plus
8,403,000 bytes in active reservations, including this 300,000-byte
documentation reservation.

## Next step

Add a v2.0.12-specific projection/adapter without changing historical
v2.0.15 receipt validation. When RAM headroom is safely above the runtime
floor, run focused source-matched checks and then a no-provider OpenCode runtime
preflight through the existing `:4000` setup. Keep paid completions closed
until a numeric campaign-wide cap is supplied and the caller's durable receipt
gate is validated. No 95% effectiveness, token reduction, cost reduction, or
all-day engineering claim is established by this iteration.
