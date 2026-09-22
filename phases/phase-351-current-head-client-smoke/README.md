# Phase 351: exact current-head client integration

Date: 2026-09-22

The package bound to commit `8d9ea2c` completed fresh read-only client
smokes. OpenCode and DeepSeek Harness both exited `0`, observed structured
read behavior, recorded three trace rows, used zero model calls, and showed
the embedded mechanical plus settlement backends.

Claude Code also exited `0` after reading `README.md` and reporting its first
heading. Its Anthropic trace recorded two rows, zero model calls, a
`2.547 ms` first-layer gate, embedded mechanical plus settlement backends,
and no mutation claim. Claude emitted a local `MiniMax-M2.7` unrecognized-model
warning, but the request completed through the loopback Wrench endpoint and
made no provider call.

This closes exact-current-head local client wiring evidence only. It does not
prove learned MiniMax parity, dense-native 4M quality, independent 5060Ti
execution, or production readiness.
