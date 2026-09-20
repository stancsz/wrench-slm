# Phase 133: package-local Ollama bridge for native backend

## Change

The portable package server now accepts an optional native upstream. The
`serve_freetoken.ps1 -OllamaApi` mode keeps FreeToken on an internal loopback
port and exposes the package-local `/api/chat`, `/api/generate`, and OpenAI
routes on the public port. Mechanical requests remain zero-model-call fast.
Native text is parsed and passed through `execute_model_output` before the
response is returned, so the native backend does not receive execution
authority.

## Verification

- Source integration test: `pytest -q tests/test_wrench_server.py`, 3 passed.
- Materializer test: `pytest -q tests/test_portable_package_materializer.py`, 5 passed.
- v45 package-local 4M probe: `PASS_MODEL_LOCAL_SERVER_4M`.
- Raw request: 4,000,000 requested tokens, 32,000,075 characters, 32,500,168
  request bytes.
- HTTP status: 200.
- Prompt estimate: 4,000,010 tokens.
- Backend: `embedded-mechanical`.
- Model calls: 0.
- Request elapsed: 109.977 ms, with the embedded server's route accounting at
  1.277 ms.

Receipt: `package-local-4m.json`.

## Boundary

This proves the new package-local bridge and direct 4M intake surface. It does
not prove stock Ollama loading, native dense 4M attention quality, MiniMax
parity, or production readiness. The native FreeToken branch still needs a
real GPU bridge smoke with the actual executable.
