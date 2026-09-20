# Phase 137: native-package 220-case replay with matched authority root

The previous v48 replay used the fixture root in the evaluator but the
repository root in the package server. That made the package's bounded
mechanical patch route unable to resolve `files/patch-*.txt`, incorrectly
sending those cases to the native upstream.

This replay binds both sides to the same
`phases/phase-120-executable-mechanical-contract/fixture` root.

## Result

- package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v48-bounded-timeout`
- launcher: `-OllamaApi -FastHistory -MoeCacheSize 16 -KvReserveTokens 1024`
- request count: 220
- outcome matches: 220/220
- exact eligible proposals: 120/120
- prohibited accepts: 0
- transport/runtime abstentions: 0
- mechanical fast-path requests: 220/220
- model calls: 0
- measured p50/p95: 0.584 ms / 45.084 ms

This is a valid package-local mechanical regression pass and fixes the prior
root-binding error. It is not evidence of native dense 4M retrieval quality,
MiniMax parity, or the frozen matched-workflow North Star gates.

The full raw receipt is `full-220-v48-correct-root.json`.
