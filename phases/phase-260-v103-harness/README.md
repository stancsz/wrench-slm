# Phase 260: v103 real harness integration

Status: local v103 smoke passed on the RTX 5070 Ti development host.

This phase verifies the current v103 model-local package, not the older v97
package. The package server was started directly from the downloaded
Safetensors directory on `127.0.0.1:28932` with the embedded mechanical route
and metadata-only trace logging enabled.

## OpenCode

The real OpenCode CLI was pointed directly at the package's OpenAI-compatible
`/v1/chat/completions` endpoint with an isolated v103 config. The normal CLI
profile was used, without `--pure` and without a proxy. The observed sequence
was:

1. OpenCode requested the native `read` tool for `README.md`.
2. Wrench returned a structured tool call.
3. OpenCode executed the local read tool.
4. Wrench returned a deterministic tool settlement.
5. OpenCode printed the final response.

The direct current v103 trace records `mechanical_fast_path=true`,
`embedded-mechanical-settlement`, zero model calls, and no file mutation. A
separate `--pure` run and a transparent proxy diagnostic also passed, but they
are supplemental evidence rather than the primary direct integration result.

## DeepSeek Harness

The real `dsh --profile headless` client was run with an isolated temporary
patch overlay and the same v103 endpoint. It completed the session-title
preflight, multi-user-role request, structured `read` call, local tool
execution, deterministic settlement, and final response. The current v103
trace records a first request of 4,889 estimated tokens with a 7.919 ms
context gate and a 0.208 ms settlement. No repository file was edited.

## Boundary discovered and verified

Normal OpenCode mode includes a large tool description bundle. On the first
attempts, words such as `delete` in that bundle correctly triggered the
fail-closed risk boundary or, when the mechanical route could not classify the
request, returned `model_not_loaded` because this smoke server was started
without a decoder. OpenCode `--pure` removes that unrelated bundle and the
same v103 package then completed the real read tool loop. This confirms the
model-local first-layer gate is active, but it also identifies a client-side
integration requirement for the normal OpenCode profile.

This is real local integration evidence on the RTX 5070 Ti development host.
It is not independent RTX 5060 Ti evidence, learned MiniMax parity,
dense-native decoder quality, Claude Code routing, or production
authorization.

Evidence:

- `receipt.json`
- `opencode-v103-direct.trace.jsonl`
- `opencode-v103-pure.trace.jsonl`
- `dsh-v103.trace.txt`
- `wrench-v103-observations-r2.jsonl`
- `wrench-v103-normal-direct-observations.jsonl`
- `wrench-v103-normal-opencode-observations.jsonl`
- `opencode-v103.json`
- `dsh-v103.patch.yml`
