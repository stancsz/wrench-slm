# Phase 267: isolated current Claude Code integration

Status: `LOCAL_CLAUDE_CODE_SMOKE_PASSED`.

The current v103 Wrench package was connected to the installed Claude Code
2.1.251 CLI through its Anthropic `/v1/messages` protocol. The run used a
fresh Claude configuration directory, a local-only auth token, the gateway
loopback settings, and a loopback proxy blocker for external traffic. The
request therefore had to reach the local Wrench endpoint or fail.

## Observed work

Claude Code performed the requested read-only `Read` operation on
`README.md`. The model-local trace contains two requests:

1. A streaming proposal request with `backend=embedded-mechanical`,
   `mechanical_fast_path=true`, and `model_calls=0`.
2. A streaming tool-result settlement with
   `backend=embedded-mechanical-settlement` and `model_calls=0`.

The first request received `249` estimated input tokens and compacted them to
`61` effective working tokens. The first-layer gate took `1.683 ms`; the
settlement took `0.010 ms`.

Claude Code exited successfully and printed the Wrench tool result. Its debug
log reported `dispatching to gateway` for both requests. No first-party
provider route or provider usage was observed in the isolated run.

This closes the current v103 local Claude Code mechanical smoke gap. It does
not prove learned MiniMax parity, native dense 4M decoder quality, independent
RTX 5060 Ti performance, or production readiness.

Evidence:

- `receipt.json`
- `wrench.trace.jsonl`
- `claude.debug.log`

