# Phase 262: Claude Code v103 routing boundary

Status: `NOT_VERIFIED`.

This phase records one isolated Claude Code 2.1.251 routing diagnostic. The
local Wrench package server was started on `127.0.0.1:28938` with the
Anthropic-compatible `/v1/messages` route and a metadata-only trace. Claude
Code was run with `--bare`, a fake `ANTHROPIC_API_KEY`, a local
`ANTHROPIC_BASE_URL`, and OAuth, Bedrock, Vertex, and Foundry environment
credentials cleared from the child process.

## Observed result

Claude Code reported:

- `apiKeySource: ANTHROPIC_API_KEY`
- model: `wrench-v103`
- `[claude-code:unrecognized_model]`
- final `provider: firstParty`
- Wrench trace rows: `0`
- provider-reported usage cost: `$0.03999`

The Claude client did perform a local-looking `Read` tool loop in its output,
but the request did not reach the local Wrench endpoint. The empty Wrench
trace is authoritative. This is not a Claude Code integration pass.

No further Claude Code attempts will be made against a real provider in this
phase. The remaining implementation work is to find a supported provider
override or build a local Claude-compatible launcher that forces the
Anthropic protocol to the model-local endpoint without provider fallback.

Evidence:

- `receipt.json`
- `claude-v103-r4.trace.jsonl` is retained locally as diagnostic output and
  is intentionally not part of the release claim.
