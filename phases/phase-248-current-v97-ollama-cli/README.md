# Phase 248: current package Ollama-compatible 4M intake

Status: the updated local package API passed a direct Ollama-shaped 4M
`/api/chat` request, and the real Ollama 0.32.13 CLI passed `show`, `list`,
and `run` against the package-local endpoint. The source fixes add the
`/api/version` probe and `HEAD /` heartbeat that the Ollama client checks
before model discovery.

## Evidence

- Package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v98-ollama-cli`
- 4M API source commit: `49952e3`
- Direct `/api/version`, `/api/tags`, and `/api/show` probes returned HTTP 200.
- Direct `/api/chat` accepted an estimated `3,999,995` token payload in a
  `32,498,051` byte request and returned HTTP 200 in `161.357 ms`.
- The first-layer gate itself took `24.894 ms`, reduced the request to 9
  effective working tokens, and recorded zero model calls.
- The route is bounded, read-only, and hash-bound. It does not claim native
  dense attention quality or MiniMax parity.

- CLI package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v100-ollama-cli`
- CLI source commit: `6a07add`
- `ollama show wrench-4b-qwen3.6-8e` returned the 4M context metadata.
- `ollama list` returned the model and digest successfully.
- `ollama run wrench-4b-qwen3.6-8e ...` returned a Wrench `read_file`
  proposal with exit code 0 and zero model calls.

This proves the model-local Ollama-compatible API and real Ollama CLI
transport. It does not prove stock Ollama native Safetensors loading or
native dense attention quality. vLLM is not installed on this host.

Evidence files:

- `ollama-v98-4m.json`
- `ollama-v98-trace.jsonl`
- `ollama-v100-cli.json`
- `ollama-v100-trace.jsonl`
