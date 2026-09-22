# Phase 345: Current-head client integration

Status: `PASSED`.

The current-head package
`D:\models\_wrench-release-candidate-ae78a84` completed read-only client
smokes through OpenCode, DeepSeek Harness, and Claude Code.

## Evidence

- OpenCode: exit code `0`, structured read observed.
- DeepSeek Harness: exit code `0`, structured read observed.
- Claude Code: exit code `0`, read-only `Read README.md` completed.
- OpenCode and DeepSeek trace: `3` rows, zero model calls, embedded mechanical
  routing, no mutation claim.
- Claude trace: `2` Anthropic Messages rows, zero model calls, first pass
  `2.734 ms`, raw input `4,139` characters, no mutation executed.
- Claude emitted one `unrecognized_model` warning for `MiniMax-M2.7`; the
  request still stayed on the local Wrench route and completed successfully.

This is current-head integration evidence, not learned MiniMax parity,
dense-native 4M quality, stock Ollama native generation, independent RTX
5060 Ti execution, or production readiness.

Evidence: `receipt.json`, `wrench-client.trace.jsonl`, and `claude.trace.jsonl`.
