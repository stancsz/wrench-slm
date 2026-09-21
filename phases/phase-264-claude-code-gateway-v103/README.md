# Phase 264: Claude Code gateway boundary on v103

Status: the direct Anthropic protocol path passes locally; the installed
Claude Code provider path remains `NOT_VERIFIED`.

## What was verified

The v103 package server was started on the RTX 5070 Ti development host with
the model-local `/v1/messages` route and metadata-only tracing enabled. A
direct Anthropic-shaped request returned HTTP 200, produced a bounded
`read_file` proposal, used the embedded mechanical backend, and recorded
`model_calls=0` in the trace.

The installed Claude Code 2.1.251 CLI was then run with the gateway-specific
environment discovered in its binary:

- `CLAUDE_CODE_USE_GATEWAY=1`
- `CLAUDE_GATEWAY_ALLOW_LOOPBACK=1`
- `ANTHROPIC_AUTH_TOKEN` set to a local-only test token
- `ANTHROPIC_BASE_URL=http://127.0.0.1:28941`
- `CLAUDE_CODE_SIMPLE=1`
- first-party provider environment variables cleared

Claude Code's debug log reported `dispatching to gateway` and issued two
`/v1/messages` requests. The Wrench trace did not gain a corresponding row,
so the request was not proven to reach the local Wrench endpoint. This is not
a Claude Code local-routing pass.

## Boundary decision

The Wrench Anthropic-compatible server is usable directly by an Anthropic
protocol client. The subscription-managed Claude Code binary still needs a
supported local provider or a separately controlled gateway that owns provider
selection. No further provider-routing attempts are authorized in this phase.

This phase does not change the existing local OpenCode, DeepSeek Harness, or
direct Anthropic protocol evidence. It also does not claim independent RTX
5060 Ti verification, learned MiniMax parity, dense-native 4M decoder
quality, or production readiness.

