# Phase 136: bounded native 220-case replay

This phase validates the public-package timeout boundary after the first
native 220-case attempt stalled behind an unbounded upstream request.

## Result

- package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v48-bounded-timeout`
- launcher: `-OllamaApi -FastHistory -MoeCacheSize 16 -KvReserveTokens 1024`
- native upstream timeout: 9 seconds
- evaluator timeout: 10 seconds
- cases: 220
- outcome matches: 200/220
- eligible exact accepts: 100/120
- prohibited accepts: 0
- transport/runtime abstentions: 20
- mechanical fast-path requests: 200/220
- measured p50/p95: 0.822 ms / 146.683 ms

The 20 misses are all `patch_draft` requests that reached the native learned
path and returned `qwen_http_error` at the bounded timeout. The result is a
diagnostic fail-closed stability pass, not a 220/220 learned-quality pass,
MiniMax parity result, or production release authorization.

The full machine-readable receipt is `full-220-v48.json`.
