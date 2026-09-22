# Phase 342: Current-head real client integration

Status: `PASSED`.

The exact release-line package
`D:\models\_wrench-release-candidate-bbc680f` handled read-only work through
the three requested client paths using local loopback endpoints.

## Evidence

- OpenCode: exit code `0`, structured read observed.
- DeepSeek Harness: exit code `0`, structured read observed.
- Claude Code: exit code `0`, read-only `Read README.md` completed.
- OpenCode and DeepSeek trace: `3` rows, zero model calls, embedded mechanical
  backend, no mutation claim.
- Claude trace: `2` Anthropic Messages rows, zero model calls, first pass
  `2.535 ms`, raw input `4,148` characters, no mutation executed.
- Claude emitted one `unrecognized_model` warning for `MiniMax-M2.7`; the
  request still stayed on the local Wrench route and completed successfully.

This proves real local client wiring and mechanical work, not learned MiniMax
parity, dense-native 4M attention quality, independent RTX 5060 Ti execution,
or production readiness.

Evidence: `receipt.json`, `wrench-client.trace.jsonl`, and `claude.trace.jsonl`.
