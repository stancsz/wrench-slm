# Phase 169: public v70 MapReduce-first package

The release path is now explicit: accept a model-local 4M request, mechanically
map and reduce old reference material, preserve the newest intent and bounded
evidence windows, then give Wrench a default 64K working context. Native direct
attention remains optional and does not block this production-value path.

## Verification

- Full repository regression: `153 passed, 14 warnings`.
- v70 structural package validation: `PASS_STRUCTURAL_PACKAGE`.
- Local v70 4M package route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`,
  `16.181 ms`, zero model calls.
- Local v70 embedded prefill stress: `PASS_EMBEDDED_MONSTER_PREFILL`,
  `352.829 ms`, zero model calls.
- Public Hub revision: `e3f5f69e1dbd685b5911509cf48f776c87e0bb03`.
- Fresh Hub download matched local SHA-256 hashes for `prefill.py`,
  `worker.py`, `toolbelt.py`, `serve_freetoken.ps1`, `README.md`, and
  `wrench-package.json`.
- Fresh launcher contains `-MoeStrategy`, `-MoeCpuLayers`, CPU-thread, and
  hybrid-fetch controls.

## Release boundary

The public artifact is an experimental, copy-pasteable Safetensors package,
not a claim of stock Ollama, vLLM, or GGUF compatibility. The 4M endpoint and
MapReduce route are verified. Native dense 2M/4M attention, MiniMax matched
workflow parity, concurrency throughput, and final production gates remain
open. The package's deterministic mechanical route can be used independently
of native model startup for eligible read-only work.
