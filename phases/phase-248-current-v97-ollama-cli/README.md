# Phase 248: current package Ollama-compatible 4M intake

Status: the updated local package API passed a direct Ollama-shaped 4M
`/api/chat` request. The source fix adds the `/api/version` probe that the
Ollama client checks before `/api/tags` and `/api/chat`.

## Evidence

- Package: `D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v98-ollama-cli`
- Source commit: `49952e3`
- Direct `/api/version`, `/api/tags`, and `/api/show` probes returned HTTP 200.
- Direct `/api/chat` accepted an estimated `3,999,995` token payload in a
  `32,498,051` byte request and returned HTTP 200 in `161.357 ms`.
- The first-layer gate itself took `24.894 ms`, reduced the request to 9
  effective working tokens, and recorded zero model calls.
- The route is bounded, read-only, and hash-bound. It does not claim native
  dense attention quality or MiniMax parity.

The installed `ollama` 0.32.13 CLI did not reach this custom host during the
same smoke attempt, so CLI-level integration remains unverified. This phase
proves the model-local Ollama-compatible HTTP API, not stock Ollama native
Safetensors loading. vLLM is not installed on this host.

Evidence files:

- `ollama-v98-4m.json`
- `ollama-v98-trace.jsonl`
