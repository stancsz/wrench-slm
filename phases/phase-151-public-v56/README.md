# Phase 151: public v56 portable package

Date: 2026-09-20

## Published artifact

The portable package was materialized from the v55 NVFP4 weights with the
shared-tokenizer launcher change and uploaded to the existing public Hub model:

- Repository: `stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M`
- Hub revision: `1c5af1683b41ae756bd434d96c19b530d4913029`
- Weight shards: unchanged
- Public format: Hugging Face Safetensors package

## Verification

- Local structural validation: `PASS_STRUCTURAL_PACKAGE`, zero errors
- Local 4M package route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`
- Local 4M route latency: `15.304 ms`
- Local mechanical model calls: `0`
- Fresh Hub downloads confirmed:
  - `serve_freetoken.ps1` contains `"--num-tokenizer", 0`
  - `README.md` documents `--num-tokenizer 0`
  - `wrench-runtime.json` records `tokenizer_processes: 0`

## Boundary

This is a public portable artifact update. It does not claim native 2M/4M
generation, dense retrieval quality, MiniMax parity, GGUF compatibility, or
production readiness. Native startup remains subject to the host's Windows
commit/pagefile state and a compatible FreeToken runtime.
