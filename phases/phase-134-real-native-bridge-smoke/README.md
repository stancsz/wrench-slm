# Phase 134: real native backend bridge smoke

## Environment

- Package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v47-ollama-native-bridge`
- Native backend: FreeToken `0.1.3+g52322e984`
- GPU: RTX 5070 Ti
- Launcher: `serve_freetoken.ps1 -OllamaApi -FastHistory -MoeCacheSize 16 -KvReserveTokens 1024`
- Public package port: `28974`
- Internal native port: `28975`

## Results

The one-command launcher reached `READY`. `/api/tags` and `/api/show` reported
the Wrench model and declared context length `4,000,000`.

The same public endpoint accepted a 37,142,960-character payload with
`options.num_ctx=4000000`:

- prompt estimate: `4,000,013`
- HTTP status: `200`
- elapsed: `128.228 ms`
- backend: `embedded-mechanical`
- model calls: `0`
- latest intent: `read_file src/wrench_harness/worker.py`

A non-mechanical request was forwarded to the real native backend:

- elapsed: `2,340.310 ms`
- backend: `native-upstream-verified`
- model calls: `1`
- verifier result: `abstain`
- reason: `model_output_invalid_json`

The generated model output was malformed, and the package correctly refused to
accept it. This is a real backend and fail-closed bridge pass, not a direct
quality pass for learned proposals.

## Boundary and operational finding

With default automatic expert-cache sizing, the first attempt failed because
the current GPU had insufficient headroom after weight/KV allocation. Manual
`MoeCacheSize=16` and `KvReserveTokens=1024` allowed the 4M native server to
start. The launcher now exposes this bounded override while retaining auto as
the default. Background GPU workloads were not terminated.

This phase proves the package-local API, real native loading, verifier routing,
and 4M mechanical intake together. It does not prove MiniMax parity, direct
dense 4M retrieval quality, or production throughput.
