# Phase 283: Claude Code local route

Date: 2026-09-21

## Scope

Close the Claude Code integration gap with a real CLI invocation, while
blocking external traffic and binding the result to the Wrench server trace.
This is a local smoke, not a provider-quality claim.

## Run

Claude Code `2.1.251` was invoked in print mode with the recognized `sonnet`
alias, an isolated config directory, loopback traffic blocker, and the local
Wrench Anthropic Messages endpoint. The temporary launcher used the current
v103 package server/runtime and did not load model weights because the request
was a deterministic read-only operation.

Prompt: `Read README.md and return a one-sentence summary.`

The CLI completed with exit code 0 and printed the Wrench tool result. The
authoritative Wrench trace contains exactly two events:

1. `protocol=anthropic-messages`, `backend=embedded-mechanical`,
   `mechanical_fast_path=true`, `model_calls=0`, `status=accepted`,
   `elapsed_ms=8.468`.
2. `backend=embedded-mechanical-settlement`, `tool_settlement`,
   `model_calls=0`, `elapsed_ms=0.026`.

Receipt trace:

- `C:\Users\stanc\AppData\Local\Temp\wrench-claude-current-v103.trace.jsonl`
- SHA-256: `87FCCCA03E03FA06ED60591F996212C75F9E1B6B3FA00CC1E64748AE4F398097`

## Boundary

Claude Code also emitted an `unrecognized_model` diagnostic for
`MiniMax-M2.7`. This is retained as a client-side warning. It does not negate
the local route because the Wrench server trace proves the request reached the
local Anthropic endpoint and the tool loop settled there. No provider request
or provider spend is claimed.

## Result

This closes the local Claude Code read-only smoke requirement for the current
v103 package. It does not prove learned native decoder quality, MiniMax parity,
or production authorization. OpenCode and DeepSeek Harness remain separately
reported in phase 260.

