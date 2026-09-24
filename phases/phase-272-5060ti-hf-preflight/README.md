# Phase 272: RTX 5060 Ti Hugging Face package preflight

Status: `PASS_HF_PACKAGE_RECEIPT`

This phase records the independent worker-side preflight for the pinned
Experimental Preview package:

- Host: NVIDIA GeForce RTX 5060 Ti
- Source commit: `6d25fc8dfa21e53c8593d4d09df7ba7f6b74e4e1`
- Hugging Face revision: `966a1720d84b330d90b6ad38f22e883e749448f3`
- Package: `stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-Experimental-Preview`
- Structural validation: passed
- Mechanical smoke: passed with an accepted proposal
- Provider spending: none
- Learned routing: disabled
- Quality, native-attention, retrieval, and production claims: not authorized

The first run exposed a Windows PowerShell 5.1 UTF-8 BOM boundary bug when
writing `resource-snapshot.json`. `tools/run_5060ti_hf_preflight.ps1` was
fixed to write BOM-free UTF-8 directly, then the complete preflight was rerun
through the fixed script and passed.

See `verified-hf-cross-host-receipt.json` for the authoritative verification
result. The package itself remains outside Git under the worker model cache.
