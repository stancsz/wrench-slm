# Wrench portable distribution

Wrench should be downloadable as one model package. Users should not need to
understand the evaluation harness, context ledger, or local development
repository.

## Package contract

The canonical Hugging Face package is a normal model directory containing:

```text
Wrench/
  config.json
  generation_config.json
  tokenizer.json
  tokenizer_config.json
  model.safetensors or model-*.safetensors
  model.safetensors.index.json       # when sharded
  modeling_wrench.py                  # only when the architecture is custom
  configuration_wrench.py             # only when the architecture is custom
  wrench_runtime/                     # bundled deterministic lookup runtime
  wrench-package.json
  README.md
  LICENSE
```

The user-facing path is one model name and one command. The runtime may contain
regex, AST, hashing, indexing, and retrieval code, but these files are shipped
inside the model package and are not a separate user-installed harness.

## Backend boundaries

The Safetensors package is the source of truth. Transformers or a compatible
custom backend can load it with the package code. vLLM and FreeToken need a
registered architecture adapter for the Wrench hybrid attention and staged
prefill behavior.

GGUF is a second distribution artifact, not a replacement for the canonical
package. GGUF stores model metadata and tensors, but does not by itself execute
Wrench's AST/search runtime. An Ollama or llama.cpp release is publishable only
after the Wrench architecture, tokenizer, hybrid KV policy, and package runtime
have been validated by that backend. Until then, do not publish a misleading
GGUF that loads but silently loses retrieval or long-context behavior.

## Long-context labels

The package must distinguish three values:

- `declared_input_context_tokens`: what the endpoint accepts;
- `native_attention_context_tokens`: what the model actually attends to without
  staged reduction;
- `effective_working_context_tokens`: the default post-retrieval model input.

The current experimental profile declares 4M endpoint input, targets 2M native
model input, and uses a 64K effective working context. The package is not
allowed to advertise native 1M or 2M until a reducer-bypassed probe records
exact model-side prompt tokens and no truncation.

## Release checklist

Before uploading a public Hugging Face revision:

1. run `tools/validate_wrench_package.py` against the exact model directory;
2. bind every shard, tokenizer, package code file, and runtime build to hashes;
3. record parameter count under 4.25B and the actual packed bytes;
4. record native attention and retrieval receipts separately;
5. include the exact one-command launch for each supported backend;
6. mark unsupported Ollama/GGUF paths as unsupported instead of silently
   falling back to a generic prompt wrapper.
