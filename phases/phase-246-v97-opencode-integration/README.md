# Phase 246: compact v97 OpenCode integration

Status: local smoke passed on the RTX 5070 Ti development host.

The current compact NVFP4 v97 package was started as a package-local Wrench
endpoint and connected to a real OpenCode CLI session through the OpenAI
compatible `/v1/chat/completions` route. OpenCode performed a real read-only
tool operation against this repository:

1. OpenCode requested the `read` tool for `README.md`.
2. Wrench emitted a structured `read` tool call.
3. OpenCode executed the tool and returned the tool result.
4. Wrench returned a deterministic settlement and OpenCode produced the final
   text response.

The Wrench trace records `mechanical_fast_path=true` for both the tool request
and the settlement, with `model_calls=0`. The successful run used the current
compact v97 package and the bundled first-layer context gate. No repository
file was edited.

This is real OpenCode integration evidence on the 5070 Ti host. It is not
independent 5060 Ti evidence, learned MiniMax parity, dense-native decoder
quality, or production authorization. Claude Code and DeepSeek Harness still
need the same current-v97 package-level verification rather than relying only
on the older v94 integration receipt.

Evidence:

- `receipt.json`
- `compact-v97-trace.jsonl`
- `../phase-244-v97-real-harness/opencode-v97.json`
