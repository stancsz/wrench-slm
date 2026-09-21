# Phase 270: portable Claude Code launcher

Status: `PORTABLE_CLAUDE_CODE_MECHANICAL_SMOKE_PASSED`.

The materializer now copies `run_claude_code.ps1` and
`wrench_loopback_blocker.py` into the downloaded model directory. The
launcher starts the package-local Wrench server, creates a fresh Claude config
directory by default, sets the supported loopback gateway environment, clears
first-party provider credentials, and routes external proxy variables to a
local fail-closed blocker.

A fresh materialized package was run on the RTX 5070 Ti development host with
the installed Claude Code CLI. The launcher performed a real read-only
`Read README.md` operation and exited successfully. The package trace recorded
two Anthropic protocol requests:

- proposal: `backend=embedded-mechanical`, `mechanical_fast_path=true`,
  `model_calls=0`, `400` estimated raw input tokens, `206` effective working
  tokens, `2.488 ms` gate latency;
- settlement: `backend=embedded-mechanical-settlement`, `model_calls=0`,
  `0.018 ms` elapsed.

This proves that the portable model directory can launch and serve a local
Claude Code mechanical path. It does not prove learned MiniMax parity,
dense-native 4M decoder quality, independent RTX 5060 Ti execution, or
production readiness.

Evidence was generated from:

- materialized package: `D:\models\_wrench-claude-launcher-materializer-check-v3`;
- package trace: `claude-launcher-smoke.trace.jsonl`;
- source changes: `packaging/run_claude_code.ps1`,
  `packaging/wrench_loopback_blocker.py`.

