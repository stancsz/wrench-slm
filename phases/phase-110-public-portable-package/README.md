# Phase 110: public portable package

## Outcome

The public Hugging Face artifact is downloadable as one model directory:

`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M`

The package contains the NVFP4 Safetensors shards, tokenizer/configuration,
bundled deterministic lookup and verifier runtime, a model-local endpoint,
FreeToken launcher, and an experimental Ollama `Modelfile`.

The public package is an experimental artifact release. It is not a claim that
native 4M attention retrieval, MiniMax parity, or production throughput has
passed.

## Verified evidence

- Local v12 materialization: `PASS_STRUCTURAL_PACKAGE`.
- Local v12 package has no `__pycache__` or `.pyc` files.
- Public Hub dry run: 35 files, approximately 3.4 GB.
- Public Hub cleanup revision: `9eab0de000f0e81e624632d0f7b80c3fb0fd7995`.
- Public copy command:

  ```powershell
  hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M
  ```

## Backend boundary

Hugging Face Safetensors is the canonical portable format. The bundled
FreeToken path is locally verified as experimental. Ollama Safetensors import
and 4M metadata import are verified, but completion on the local Ollama build
is blocked by its MLX runner selection. vLLM requires a registered Wrench
architecture adapter. GGUF is not published because a generic conversion
would not preserve the Wrench hybrid attention, staged prefill, and lookup
semantics.

## Reproduction

```powershell
python tools/validate_wrench_package.py `
  --model-dir D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-fast-history-auto-smoke-v12 `
  --output phases/phase-110-public-portable-package/portable-package-v12-validation.json
```
