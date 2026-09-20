# Phase 209: v85 one-command portable smoke

Date: 2026-09-20

The downloaded v85 package was started with its own launcher only:

```powershell
.\run_wrench.ps1 -Port 28930 -AllowedRoot D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v85-ollama-boundary
```

No repository `PYTHONPATH` or external harness was supplied. The package
reported `READY`, `/api/show` returned a declared context length of 4,000,000
and an effective working context of 64,000, and an Ollama-shaped `/api/chat`
request with `options.num_ctx=4000000` returned a valid read proposal through
the embedded mechanical route:

- backend: `embedded-mechanical`;
- model calls: 0;
- action: `read_file`;
- path: `README.md`;
- byte limit: 4,096.

This proves the copy-paste package path and direct model-local API surface for
mechanical work. It does not change the separate stock-Ollama NVFP4 generation
quality failure recorded in Phase 207.
