# OpenCode-compatible SSE encoder contract evaluation

Job: `W2-NS-OPENCODE-SSE-CONTRACT-20260924`, nonce `OSC-1D7B`  
Reviewed base: `c1342ef`

## Decision

Accept the bounded unit-test slice. The synthetic fixture verifies the
non-tool Chat Completions event order and `[DONE]` framing implemented by
`_completion_stream_chunks`. The implementation matched the expected local
success shape; no production source changes were needed.

## Evidence

- The new test calls the encoder directly and checks assistant role, content,
  stop finish reason, per-event SSE framing, and final `[DONE]`.
- `python -m pytest -q tests/test_wrench_server.py`, run using the provisioned
  Python 3.11.16 and cached pytest 8.4.2, completed with **18 passed**.
- `git diff --check` passed, with only the line-ending conversion warning.
- No OpenCode request, model inference, provider call, install, or download was
  performed. The test itself is socket-free; other pre-existing tests in the
  focused file start ephemeral Wrench loopback servers.

## Scope limits

The fixture covers one synthetic, non-tool completion. It does not validate
malformed completion handling, empty content, the live OpenCode parser or
runtime, port routing, hook behavior, provider/tokenizer parity, or E0/E4
acceptance. See the [source report](../../reports/wrench-e0-opencode-context-adapter/sse-contract.md)
and the pre-existing [mock-runtime preflight](../../reports/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md)
for those boundaries.
