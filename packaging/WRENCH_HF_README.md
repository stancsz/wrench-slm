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

This Hub repository contains the NVFP4 native-4M experimental candidate,
distributed as one copy-pasteable portable package. Its candidate identity is
`Wrench-4B-Qwen3.6-8E-Safety-v7-NVFP4-native4M`.

Wrench is a pruned, task-specific developer-tool SLM derived from Qwen3.6-35B-A3B.
It contains 3,881,244,016 parameters and stays below the 4.25B parameter ceiling.

This is a public experimental artifact. It is downloadable and reproducible, but
it is not a claim that the final 4M retrieval-quality, MiniMax-parity, or
production-throughput gates have passed. The package still requires the complete
matched 220-case release evaluation.

## Copy the package

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M
```

On Windows, start the downloaded package with one command:

```powershell
cd .\Wrench-4B-Qwen3.6-8E-NVFP4-native4M
.\run_wrench.ps1
```

This starts the bounded mechanical endpoint at
`http://127.0.0.1:28900`. Add `-LoadModel` only when the local model backend
is configured and ambiguous requests should load the checkpoint.

The canonical distribution format is Hugging Face Safetensors. The package embeds
the tokenizer hook, deterministic mechanical lookup runtime, read-only verifier,
long-context overlay, hash-bound package metadata, and the FreeToken launcher. It
is intended to feel like one model directory, not a separately installed harness.

The bundled FreeToken launcher enables the package-local mechanical route for
high-confidence read-only proposals. Those requests return a standard chat
completion with `model_calls=0`; ambiguous requests continue through the model.
Every proposal remains subject to an independent verifier before execution.
Simple reads without an explicit byte limit use the verifier's bounded 256 KiB
cap. Requests asking for the entire or complete file remain fallback-required
so a large file is never silently truncated.

For `patch_draft`, the verifier requires a real review-only unified diff with
actual added or removed content. Header-only or empty diffs are rejected as
`invalid_patch_diff`; a schema-valid empty patch is never reported as useful
work.

When a request contains one explicit quoted text operation, such as
`Replace "old" with "new" in README.md`, `Append "line" to README.md`, or
`Insert "line" after "anchor" in README.md`, the embedded route reads that one
file, constructs a review-only unified diff, and leaves the working tree
untouched. It supports replace, append, prepend, insert-after, and remove
when the text match is unique. Ambiguous or under-specified patch requests
return `patch_content_missing` without spending a model call.

The embedded worker API is available directly from the downloaded directory:

```python
from wrench_worker import WrenchWorker

worker = WrenchWorker.from_pretrained(
    "./Wrench-4B-Qwen3.6-8E-NVFP4-native4M", load_model=False
)
result = worker.propose([
    {"role": "user", "content": "Read README.md with a 65536 byte limit."}
])
```

## Run it as a local model endpoint

The package also contains its own small OpenAI-compatible server. It accepts
the complete raw request at the model endpoint, then applies the bundled
mechanical route or bounded working-context reducer inside the package:

```powershell
python .\wrench_server.py --model-dir . --allowed-root . --mechanical-only
```

The endpoint is `http://127.0.0.1:28900/v1/chat/completions`. A client can send
the full conversation, including a multi-million-token raw payload, directly to
this model-local process. The response includes the raw input estimate,
effective route, model-call count, and dynamic-prefill receipt. Remove
`--mechanical-only` when the local backend is ready to load the model weights.

The same process exposes a small Ollama-compatible local surface for clients
that expect Ollama-shaped requests:

```powershell
curl http://127.0.0.1:28900/api/tags
curl http://127.0.0.1:28900/api/show -d '{"name":"wrench-4b"}'
curl http://127.0.0.1:28900/api/chat -d '{"model":"wrench-4b","messages":[{"role":"user","content":"Read README.md with a 4096 byte limit."}],"stream":false,"options":{"num_ctx":4000000}}'
```

This is an Ollama API compatibility layer inside the downloaded package. It
does not claim that stock Ollama can load the Wrench hybrid checkpoint or that
a generic GGUF conversion preserves the package-local toolbelt.

The bundled FreeToken launcher pins the 4M KV capacity explicitly and uses an
automatic expert cache. This avoids allocating an oversized sparse address
mapping on GPUs with limited memory. It improves the native serving profile,
but it does not by itself prove fast dense generation at 4M.

The launcher uses FreeToken's `--num-tokenizer 0` shared-tokenizer mode. This
avoids an extra Torch tokenizer process and lowers Windows startup memory
pressure when the native model is loading CUDA libraries.
It also uses `--expert-load serial` to avoid a parallel whole-shard host-memory
buffer while loading the MoE experts.
The launcher constrains BLAS thread pools to one thread and enables lazy CUDA
module loading for lower-memory Windows startup.
Failed native smoke startup also cleans the complete FreeToken process tree to
avoid leaking Torch workers into subsequent launches.

To expose the native FreeToken backend through the same package-local
Ollama-shaped endpoint, use:

```powershell
.\serve_freetoken.ps1 -OllamaApi -AllowedRoot C:\path\to\your\repo
```

This keeps FreeToken on a private loopback port and starts the bundled Wrench
server on the public port. Mechanical requests are handled inside the package;
other native responses pass through the bundled verifier before they are
returned. It is still a package adapter around the experimental FreeToken
backend, not a claim that stock Ollama loads the Wrench architecture.

On a GPU with competing workloads, override the automatic expert-cache planner
instead of changing the model package:

```powershell
.\serve_freetoken.ps1 -OllamaApi -MoeCacheSize 16 -KvReserveTokens 1024
```

`MoeCacheSize` must be at least 16 for this 8-expert package. The default
remains automatic sizing.

The package bridge bounds a native upstream request to 9 seconds by default,
so one slow or malformed native generation cannot stall the whole mechanical
worker. Override `-UpstreamTimeoutSeconds` only when the caller uses a longer
matching timeout.

When `-OllamaApi` is enabled, the launcher performs a real native completion
smoke test before starting the public package server. A `/v1/models` response
alone is not sufficient readiness. Startup diagnostics are saved in
`native-startup.log` and `native-startup-error.log`, and a failed native
backend prevents a misleading healthy API from starting.

For an experimental faster native profile that treats old history as
reference-only, use:

```powershell
.\serve_freetoken.ps1 -FastHistory -FastHistoryKeepTokens 64000
```

When the native endpoint is serving a user's repository, point the embedded
mechanical route at that repository explicitly:

```powershell
.\serve_freetoken.ps1 -AllowedRoot C:\path\to\your\repo
```

The root is read-only proposal scope. Wrench never applies a patch; the
external verifier remains responsible for approval and execution.

This keeps the complete raw request and model-side prompt accounting for the
actual request length, then skips attention and MLP work before the recent-token
boundary. It therefore scales between 2M and 4M requests. It is opt-in
because retrieval quality and MiniMax parity for this policy are not yet
verified. The default launcher does not enable it.

This endpoint is part of the downloaded package, not a separately installed
Wrench harness. It still does not claim dense native attention quality over
every 4M token. It provides the practical model-local path while that native
quality and throughput work continues.

The current boundary-repaired runtime has also passed a direct native
3,995,331-token provider probe: HTTP 200, `truncated=false`, and
`native_context_pass=true` at a configured 4,000,000-token limit. The measured
single-request prefill was 173,384.564 ms on the development RTX 5070 Ti with
the default 64K recent tail. This is a capacity and serving-path result, not a
claim of general retrieval quality or MiniMax parity.

With `load_model=True`, ambiguous requests use the standard Transformers model
and still pass through the same fail-closed verifier. High-confidence
mechanical requests use the embedded route without a model call.

For a large multi-turn payload, the package worker applies the bundled
deterministic staged prefill before model generation. Old user and assistant
messages become hash-bound reference cards, the newest user message remains the
active intent, and the default model working budget is 64K estimated tokens.
The returned result includes a `dynamic_prefill` receipt. This is a bounded
working-context optimization, not a claim that dense attention was performed
over every 4M token. If an application sends the whole conversation as one
large user message, the package splits the old prefix from the newest suffix
internally before building the same reference index.

In `-OllamaApi` mode this reducer is embedded in the downloaded package server.
The server accepts the original request, stages it deterministically, and sends
the staged messages to the internal native backend while keeping the original
payload hash and latest intent for verification. A fresh 4M worker stress run
reduced the raw input to a bounded prefill with zero model calls. That run took
92.763 ms locally. A real package-server handoff probe measured 85.714 ms for
server-side staging, separate from raw HTTP intake and the protocol-stub round
trip. This proves the staging shape, not dense native 4M attention.

For the standard Hugging Face config and tokenizer path, use Transformers 5.17.0
or newer:

```powershell
python -m pip install -U "transformers>=5.17.0" huggingface_hub
```

## Run the experimental native endpoint

The bundled launcher requires a compatible FreeToken build and a CUDA GPU:

```powershell
.\serve_freetoken.ps1
```

The package declares a 4M input endpoint and uses an 8K recent SWA window in the
experimental native profile. The bundled launcher pins a 4M KV capacity and
uses FreeToken's automatic expert cache with an 8K reserve. The default
`-OllamaApi` path mechanically reduces noisy payloads to a 64K effective
working context. Use `-NativeDirectInput` to send the complete raw request to
the native backend. Native direct input and fast staged input are recorded
separately in receipts.

The embedded reducer has also passed a 4M mechanical stress diagnostic: 3,999,951
estimated raw tokens reduced to a 92-token model prefill, with 1.0 target-reference
recall, 1.0 current-intent preservation, and 1.0 hash-bound reference rate. The
measured cold ingest was 98.713 ms and hot selection was 44.441 ms on the local
development machine. This is deterministic toolbelt evidence, not an LLM
long-context quality or MiniMax-parity claim.

The embedded native endpoint also passes deterministic history lookup canaries:
an approximately 2M-token request completed in 112.471 ms and an approximately
4M-token request completed in 460.155 ms, both recovering
`src/wrench_harness/worker.py` from old reference material with zero model calls.
These canaries validate the bounded lookup route only. They do not establish
general native attention retrieval quality or MiniMax parity.

## Backend status

- Hugging Face Safetensors: public experimental package. Transformers 5.17.0+
  recognizes the bundled Qwen3.5 MoE architecture and Wrench tokenizer metadata.
- FreeToken: locally verified experimental backend.
- The bundled FreeToken path has produced a schema-valid read-only proposal on a
  small smoke request when given the explicit Wrench output contract.
- vLLM: requires a registered Wrench architecture adapter.
- Ollama: the public v42 metadata is text-only and imports through the
  Safetensors path. An isolated Windows MLX runner loaded the model and
  completed a short request after a local cuDNN path workaround. Stock Windows
  Ollama completion is still not verified.
- llama.cpp and GGUF: not verified for Wrench hybrid attention and lookup
  semantics. Do not assume a generic GGUF conversion preserves these features.

The package also includes an experimental Ollama `Modelfile`. Ollama 0.34.2+
can attempt local Safetensors import with `ollama create --experimental`.
Windows users still need the matching MLX CUDA runner and cuDNN runtime. The
portable package does not patch or install third-party runtime binaries.

GGUF is not a file-extension conversion. A valid GGUF release needs a tested
llama.cpp or Ollama architecture adapter, tokenizer mapping, hybrid KV policy,
and bundled lookup semantics. Until that adapter is verified, Hugging Face
Safetensors is the canonical copy-paste format.

## Known limits

The base checkpoint config is 2M position-capable. The 4M probe uses a runtime RoPE
extension and is not long-context training. Native 4M retrieval quality, throughput
under production concurrency, and the full MiniMax matched-workflow acceptance suite
remain open measurements. The current native fast-history profile is still
experimental and opt-in.

The standard Transformers path has verified architecture/configuration,
tokenization, and full weight loading. Generation quality through plain
Transformers is not yet a pass and is intentionally not claimed here. Use the
bundled FreeToken profile for the current experimental generation path.

Wrench has no direct mutation authority. It proposes bounded developer-tool actions
or abstains; a surrounding verifier must enforce execution policy.
