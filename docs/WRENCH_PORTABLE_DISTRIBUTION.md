# Wrench portable distribution

Wrench should be downloadable as one model package. Users should not need to
understand the evaluation harness, context ledger, or local development
repository.

The current public Experimental Preview package is
`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview`. Copy it with:

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview
```

This is an Experimental Preview artifact, not a production-readiness
declaration. Do not deploy it in production or safety-critical workflows.

The user-facing Wrench value is the embedded hybrid long-context worker. The
package accepts a raw 2M or 4M logical payload at its own model-local endpoint,
then uses deterministic MapReduce, AST/search extraction, bounded lookup cards,
and verification to keep the effective model working context small and fast.
Dense native attention over every raw token is an optional research comparison,
not a product selling point or release gate.

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
    ttc.py                             # bounded test-time-compute verifier
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
claim that stock Ollama can run the Wrench hybrid checkpoint. A real Ollama
0.34.2 MLX importer did import the v84 Safetensors package, preserved its
3.4B NVFP4 architecture, loaded 3,993 tensors, and reported a 4,000,000-token
context. A patched relocatable CUDA runtime then reached real generation, but
the short `/api/generate` result was empty after 16 generated tokens, and
`/api/chat` with `think=false` returned malformed repeated-token text after 64
generated tokens. Stock Ollama import and metadata are therefore verified, but
native generation quality is not passed. The package-local hybrid endpoint
remains the supported production-shaped path.

In `-OllamaApi` mode the reducer is embedded in the downloaded package server.
The map stage builds content-addressed lookup cards and the reduce stage keeps
the latest intent, hot context, matching cards, and bounded evidence windows.
The server accepts the original request, sends only the staged messages to the
internal native backend, and returns an original-payload hash plus a prepared-
payload hash. This provides a practical 4M-to-64K native handoff, but it is
not dense attention over every raw token. The current fast-first-layer package
reduced about 4M estimated tokens to 1,955 staged tokens. Three fresh
Ollama-shaped `/api/chat` runs measured 81.003 ms, 97.351 ms, and 99.029 ms
for server-side staging on the development host. Complete local protocol-stub
round trips were 186.708 ms to 214.542 ms because the request still transfers
about 35 MB on localhost. This is still not dense native 4M attention.

The native handoff index is content-addressed and can persist across requests
inside the package server. Its byte ceiling is configurable with
`WRENCH_PREFILL_CACHE_BYTES` or the server's `--prefill-cache-bytes` option.
The default is 256 MiB. A zero value disables retention while preserving the
same bounded request behavior. Runtime receipts expose cache entries, bytes,
hits, and misses so a larger cache can be used only when the host has memory.

The same embedded lookup path can recover an exact unified diff from an older
reference when the newest request asks for an unapplied review-only patch. It
requires matching paths, a valid hunk, bounded size, and an existing file. If
the old context does not contain the exact diff, Wrench abstains instead of
inventing one. The proposal remains review-only and is never applied.

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
portable package server honors the same switch and records the mode in its
receipt, so a fast result cannot be reported as native-input evidence.

The generated launcher defaults to fast staged mode with `-OllamaApi`. To send
the complete raw request directly into the native backend, use:

```powershell
.\serve_freetoken.ps1 -OllamaApi -NativeDirectInput
```

That direct mode is the required path for a native-context capability probe. It
may be slower and remains subject to the backend's real memory and
retrieval-quality evidence.

On Windows, the bundled launcher defaults to `ft.cmd`, which is the command
wrapper installed by the current FreeToken distribution. Use
`-FreeTokenExecutable` to point at a different compatible binary or wrapper.

The bundled FreeToken launcher pins a 4M KV capacity and uses automatic
expert-cache sizing with an 8K reserve for the pure-SWA profile. Adjust the
launcher's `-KvReserveTokens` when the target GPU has a different memory
budget.

The launcher passes `--num-tokenizer 0` to FreeToken. This shares tokenization
with the detokenizer instead of starting another Torch worker, which reduces
Windows startup memory pressure while preserving the native request path.
It also passes `--expert-load serial` so MoE shard loading does not allocate a
parallel whole-shard buffer during startup.
The native launcher constrains BLAS thread pools to one thread and enables lazy
CUDA module loading to avoid a second host-memory spike during Windows worker
startup.
When the native smoke fails, the package launcher terminates the complete
FreeToken process tree so failed probes do not leak Torch workers into later
starts.

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

If the machine has less free GPU memory than the default offload profile,
the launcher exposes bounded expert-placement profiles without changing the
model package or granting mutation authority:

```powershell
.\serve_freetoken.ps1 -OllamaApi -NativeDirectInput -MoeStrategy cpu -MoeCpuThreads 4
```

`cpu` keeps expert computation on the CPU and is intended as a startup
fallback on a busy GPU. `hybrid` and `-MoeCpuLayers` are also available for
controlled experiments. These profiles still need enough host RAM, pagefile,
and CUDA headroom for the attention and embedding layers. A startup failure is
reported and the child process tree is cleaned up. The current development
machine was too full to prove native generation with this profile, so this is
a launcher capability receipt, not a native quality or throughput claim.

The native bridge defaults to a 9-second upstream timeout. Keep the caller's
request timeout longer than this bound so a slow native generation fails closed
without blocking later mechanical requests.

In `-OllamaApi` mode the launcher now requires a real native completion smoke
request before exposing the package API. `/v1/models` alone is not treated as
model readiness. Native stdout and stderr are captured as
`native-startup.log` and `native-startup-error.log`; a failed backend exits
without publishing a misleading healthy API port.

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
