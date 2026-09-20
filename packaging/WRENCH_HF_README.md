---
library_name: transformers
license: apache-2.0
pipeline_tag: text-generation
tags:
- wrench
- code
- developer-tools
- qwen3.6
- long-context
---

# Wrench-4B-Qwen3.6-8E

Wrench is a pruned, task-specific developer-tool SLM derived from Qwen3.6-35B-A3B.
It contains 3,881,244,016 parameters and stays below the 4.25B parameter ceiling.

This is a public experimental artifact. It is downloadable and reproducible, but it
is not a claim that the final 4M retrieval-quality or MiniMax-parity gates have
passed.

## Copy the package

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E --local-dir Wrench-4B-Qwen3.6-8E
```

The canonical distribution format is Hugging Face Safetensors. The package embeds
the tokenizer hook, deterministic mechanical lookup runtime, read-only verifier,
long-context overlay, hash-bound package metadata, and the FreeToken launcher. It
is intended to feel like one model directory, not a separately installed harness.

## Run the experimental native endpoint

The bundled launcher requires a compatible FreeToken build and a CUDA GPU:

```powershell
.\serve_freetoken.ps1
```

The package declares a 4M input endpoint and uses an 8K recent SWA window in the
experimental native profile. The default fast path mechanically reduces noisy
payloads to a 64K effective working context. Native direct input and fast staged
input are recorded separately in receipts.

The embedded reducer has also passed a 4M mechanical stress diagnostic: 3,999,951
estimated raw tokens reduced to a 92-token model prefill, with 1.0 target-reference
recall, 1.0 current-intent preservation, and 1.0 hash-bound reference rate. The
measured cold ingest was 98.713 ms and hot selection was 44.441 ms on the local
development machine. This is deterministic toolbelt evidence, not an LLM
long-context quality or MiniMax-parity claim.

## Backend status

- Hugging Face Safetensors: public experimental package.
- FreeToken: locally verified experimental backend.
- vLLM: requires a registered Wrench architecture adapter.
- Ollama, llama.cpp, and GGUF: not verified for Wrench hybrid attention and lookup
  semantics. Do not assume a generic GGUF conversion preserves these features.

## Known limits

The base checkpoint config is 2M position-capable. The 4M probe uses a runtime RoPE
extension and is not long-context training. Native 4M retrieval quality, throughput
under production concurrency, and the full MiniMax matched-workflow acceptance suite
remain open measurements.

Wrench has no direct mutation authority. It proposes bounded developer-tool actions
or abstains; a surrounding verifier must enforce execution policy.
