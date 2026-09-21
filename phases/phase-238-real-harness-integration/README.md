# Phase 238: real harness integration

Status: local integration slice passed on the RTX 5070 Ti development host.

This phase makes the model-local Wrench endpoint usable by real coding
harnesses. The endpoint remains a bounded proposal service. It does not run
shell commands, write files, or obtain credentials.

## Verified paths

| Client | Protocol | Real work observed | Wrench result |
| --- | --- | --- | --- |
| OpenCode | OpenAI `/v1/chat/completions` | OpenCode executed one native `read` tool call against `README.md` | one mechanical proposal, one settlement, zero model calls |
| Claude Code | Anthropic `/v1/messages` | Claude Code executed one native `Read` tool call against `README.md` | one `tool_use`, one `tool_result` settlement, zero model calls |
| DeepSeek Harness | OpenAI `/v1/chat/completions` | isolated `dsh --profile headless` read `README.md` through its local filesystem tool | one pre-assistant mechanical proposal, one settlement, zero model calls |

DeepSeek Harness adds several user-role system snapshots before its first
assistant turn. The worker now recognizes that pre-assistant bundle and keeps
the first explicit routine intent ahead of wrapper text. Its session-title
preflight is answered deterministically so skill descriptions cannot trigger a
literal-search proposal.

## Boundary behavior

- OpenAI streaming emits valid tool-call SSE and settlement text.
- Anthropic streaming emits `message_start`, content block, delta, block stop,
  message delta, and message stop events.
- Only read/search proposals can become client-native tool calls.
- Edit, write, shell, and mutation-like tools are never synthesized.
- Returned tool content is bounded to 16,384 characters and is treated as
  client-authoritative display data, not execution authority.
- A model call remains at zero for all three smoke paths because each request
  used the deterministic mechanical route.

## Regression and package evidence

- Source regression: `171 passed, 14 warnings`.
- A new portable package was materialized at
  `D:\models\Wrench-Qwen3.6-8expert-BF16-hybrid-v94-harness`.
- The package-local OpenAI round trip passed: `read` tool call followed by
  `embedded-mechanical-settlement`, zero model calls.
- Package parameters remain `3,881,244,016`, below the 4.25B ceiling.

This phase is not 5060 Ti evidence, learned MiniMax parity, dense native 4M
attention quality, or production release authorization. The independent 5060
Ti queue remains a separate required verification lane.
