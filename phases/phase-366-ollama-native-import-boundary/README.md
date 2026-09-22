# Phase 366: Stock Ollama native import boundary

Date: 2026-09-21

Status: `FAIL_OLLAMA_NATIVE_IMPORT_METADATA`

An actual `ollama create` was attempted with Ollama `0.32.13` and the
package's shipped `Modelfile` using `FROM .`. The converter copied the package
components, then failed during conversion with:

`missing fp8 block size metadata for tensor "model.language_model.layers.0.linear_attn.in_proj_qkv.weight_scale"`

No model with the attempted name was left in `ollama list`. Existing Ollama
models were not modified or removed.

This is a real native-import failure for the current NVFP4 Safetensors path.
The verified product lane remains the bundled Wrench model-local runtime and
its Ollama-shaped endpoint. Native stock Ollama import is not claimed until the
required quantization metadata and architecture conversion path are fixed.
