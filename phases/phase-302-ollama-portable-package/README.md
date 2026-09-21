# Phase 302: Ollama-shaped portable package acceptance

## Result

The downloaded package was started directly from
`D:\models\_wrench-current-client-20260921` through its bundled
`wrench_server.py`. The package-local Ollama-shaped surface passed:

- `/api/version` reports `ollama-compatible`
- `/api/tags` returns the Wrench model catalog
- `/api/show` declares a 4,000,000-token context length
- `/api/chat` accepts a small request with `options.num_ctx=4000000`
- `/api/chat` accepts a 4M-configured monster request with 3,995,426 estimated
  raw input tokens
- the monster request is hash-bound, uses the embedded mechanical path, makes
  zero model calls, and compacts to a 9-token effective working context
- monster request elapsed time was 275.954 ms
- RAM availability remained 47.71 percent after the run

Receipt: `ollama-portable-package-receipt.json`

## Boundary

This proves direct model-local Ollama-shaped raw intake and deterministic
reduction in the downloaded package. It does not prove dense-native 4M
attention, learned MiniMax parity, independent RTX 5060 Ti verification, or
production readiness.

## Reproduction

```powershell
python tools/smoke_ollama_portable_package.py `
  --package-dir D:\models\_wrench-current-client-20260921 `
  --output phases\phase-302-ollama-portable-package\ollama-portable-package-receipt.json
```
