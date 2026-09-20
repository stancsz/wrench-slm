# Wrench portable distribution

Wrench should be downloadable as one model package. Users should not need to
understand the evaluation harness, context ledger, or local development
repository.

The current public experimental package is
`stancsz/Wrench-4B-Qwen3.6-8E`. Copy it with:

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E --local-dir Wrench-4B-Qwen3.6-8E
```

This is a public artifact release, not a production-readiness declaration.

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
  tokenization_wrench.py              # bundled long-context tokenizer hook
  wrench_prefill.py                   # dynamic-module-local dependency
  wrench_mechanical.py                # bundled high-confidence mechanical router
  wrench_toolbelt.py                  # bundled read-only verifier and executor
  modeling_wrench.py                  # only when the architecture is custom
  configuration_wrench.py             # only when the architecture is custom
  wrench_runtime/                     # bundled deterministic lookup runtime
    toolbelt.py                        # same verifier for package-local imports
    mechanical.py                      # bounded no-model route
    worker.py                           # embedded worker API
  wrench_worker.py                     # convenience import
  wrench-runtime.json                 # fast/native mode contract
  serve_freetoken.ps1                 # native 4M experimental launcher
  wrench-package.json
  README.md
  LICENSE
```

The user-facing path is one model name and one command. The runtime may contain
regex, AST, hashing, indexing, and retrieval code, but these files are shipped
inside the model package and are not a separate user-installed harness.

The portable worker can be used directly from the downloaded directory:

```python
from wrench_worker import WrenchWorker

worker = WrenchWorker.from_pretrained("./Wrench", load_model=False)
proposal = worker.propose([
    {"role": "user", "content": "Read README.md with a 65536 byte limit."}
])
```

The worker routes high-confidence mechanical requests through the embedded
deterministic path. Ambiguous requests can set `load_model=True` and use the
standard Transformers model, with every output still passing the verifier.

For a local Hugging Face directory, the embedded hook is loaded through the
normal Transformers API:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(
    "./Wrench", trust_remote_code=True, local_files_only=True
)
```

Use Transformers 5.17.0 or newer for the Qwen3.5 MoE architecture in this
checkpoint. The config and tokenizer mapping are verified with that runtime;
full generation still requires a compatible GPU backend.

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

The bundled tokenizer has two explicit modes. The default fast mode performs
mechanical 4M-to-64K staging. Setting `WRENCH_NATIVE_DIRECT_INPUT=1` disables
that staging and sends the complete chat payload to the backend tokenizer. The
portable package records which mode was used in its receipt, so a fast result
cannot be reported as native-input evidence.

The bundled FreeToken launcher enables native direct mode and uses an explicit
16-slot MoE cache for the pure-SWA profile. FreeToken's automatic MoE cache
sizing currently assumes a full-attention group and is not compatible with the
zero-full-layer capacity profile. Adjust the launcher's `-MoeCacheSize` when
the target GPU has a different memory budget.

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

For every public Hugging Face revision:

1. run `tools/validate_wrench_package.py` against the exact model directory;
2. bind every shard, tokenizer, package code file, and runtime build to hashes;
3. record parameter count under 4.25B and the actual packed bytes;
4. record native attention and retrieval receipts separately;
5. include the exact one-command launch for each supported backend;
6. mark unsupported Ollama/GGUF paths as unsupported instead of silently
   falling back to a generic prompt wrapper.
