# Wrench portable distribution

Wrench should be downloadable as one model package. Users should not need to
understand the evaluation harness, context ledger, or local development
repository.

The current public experimental package is
`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M`. Copy it with:

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M
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
  toolbelt.py                         # dynamic-module import target
  core.py                             # dynamic-module verifier dependency
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

On Windows, the downloaded directory can be started with one command:

```powershell
.\run_wrench.ps1
```

This starts the bounded mechanical endpoint on `http://127.0.0.1:28900`.
Pass `-LoadModel` only when the local Transformers backend is configured and
you want ambiguous requests to load the checkpoint.

The package-local server also exposes a small Ollama-compatible surface at
`/api/tags`, `/api/show`, `/api/chat`, and `/api/generate`. The `/api/chat`
route accepts `options.num_ctx=4000000` while keeping the complete request
inside the package-local reducer. This is an API compatibility layer, not a
claim that stock Ollama can load the Wrench hybrid checkpoint.

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
An uncomplicated read with no byte limit uses a 256 KiB verifier cap; requests
for the entire or complete file remain model/fallback-required.

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

The bundled FreeToken launcher enables native direct mode, pins a 4M KV
capacity, and uses automatic expert-cache sizing with an 8K reserve for the
pure-SWA profile. Adjust the launcher's `-KvReserveTokens` when the target GPU
has a different memory budget.

To keep the native backend inside the downloaded model package while exposing
the package-local Ollama-shaped API, run:

```powershell
.\serve_freetoken.ps1 -OllamaApi -AllowedRoot C:\path\to\your\repo
```

FreeToken listens only on an internal loopback port. The bundled Wrench server
owns the public port, routes high-confidence mechanical work locally, and
verifies native backend text before returning it. This remains an experimental
package adapter, not stock Ollama architecture support.

If another GPU workload leaves too little headroom for automatic expert-cache
sizing, use the bounded manual cache profile:

```powershell
.\serve_freetoken.ps1 -OllamaApi -MoeCacheSize 16 -KvReserveTokens 1024
```

The default launcher still uses automatic cache sizing.

The native bridge defaults to a 9-second upstream timeout. Keep the caller's
request timeout longer than this bound so a slow native generation fails closed
without blocking later mechanical requests.

For an experimental faster native profile that treats old history as
reference-only, use:

```powershell
.\serve_freetoken.ps1 -FastHistory -FastHistoryKeepTokens 64000
```

For native mechanical proposals against a local checkout, pass its explicit
read-only root:

```powershell
.\serve_freetoken.ps1 -AllowedRoot C:\path\to\your\repo
```

The default root is the current directory. The launcher passes this root to
the embedded route and patch verifier without granting mutation authority.

This keeps the complete raw request and model-side prompt accounting for the
actual request length, then skips attention and MLP work before the recent-token
boundary. It therefore scales between 2M and 4M requests. It is opt-in
because retrieval quality and MiniMax parity for this policy are not yet
verified. The default launcher does not enable it.

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
