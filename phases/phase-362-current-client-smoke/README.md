# Phase 362: OpenCode and DeepSeek Harness client smoke

Date: 2026-09-21

Status: `PASSED_LOCAL_CLIENT_SLICE`

The downloaded Wrench package was exercised through its real model-local
OpenAI-compatible server by both supported clients:

- OpenCode: exit code 0, structured read observed.
- DeepSeek Harness: exit code 0, structured read observed.
- Trace: 3 rows, `openai-chat-completions`, embedded mechanical route plus
  embedded settlement, 0 model calls, and no mutation claim.

The run used a temporary workspace and port 28901. The generated receipt,
client outputs, and trace are under `run/`.

This proves a real local client integration slice. It does not prove
independent RTX 5060 Ti execution, learned MiniMax parity, dense-native 4M
decoder quality, or production readiness.
