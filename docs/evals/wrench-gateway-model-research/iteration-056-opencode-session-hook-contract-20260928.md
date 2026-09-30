# Iteration 056: pin the session-profile key to the OpenCode V2 contract

## Primary-source finding

The current OpenCode V2 plugin reference defines `SessionContextHook` as a
`SessionRequestHook` plus the agent and mutable tool map. The request hook
includes a read-only `sessionID`. The reference says `context` runs for the
agent loop, including tool-driven continuations, and that hooks run in
registration order. This supports keying a frozen profile by the session ID
instead of rerunning the selector for every request.

Source: [OpenCode V2 plugin hooks](https://opencode.ai/v2/docs/build/plugins).
This is the current public contract. It does not confirm the hook payload or
ordering of the installed v2.0.12 package.

## Engineering decision

Updated the disabled OpenCode prototype README with the state and recovery
contract for the next implementation:

- Select once for each session and reuse while the full inventory hash is
  unchanged.
- Pass through the complete tool map when session identity is missing, the
  inventory changes, or bounded session state has been evicted.
- Keep each reviewed profile's required execution and verification tools.
- Restore omitted schemas only through a helper bounded by the original
  hash-bound inventory and explicit per-request, per-session, and byte/token
  limits. Record each expansion and cache-key transition.
- Do not change native permissions or tool implementations.

The prototype remains disabled and unregistered. Next implement this contract,
then verify the actual v2.0.12 event, ordering, and final lowered request in a
no-provider harness before any paid comparison.

## Current gates

At the fresh sample, free RAM was 3,215.9 / 32,701.8 MiB (9.83%), below the
10% reserve. The RTX 5060 Ti showed 15,229 / 16,311 MiB free. No tests,
OpenCode runtime, inference, training, benchmark, packaging, or delegation
ran. No provider request or spend occurred. The local SubRoute at
`http://127.0.0.1:4000` remains the required comparison gateway; its active
forced route still requires a numeric campaign cap before generation.

This API-contract update establishes no Wrench token, quality, cost, LoRA,
95/5 routing, or sustained-engineering result. Those targets remain open.
