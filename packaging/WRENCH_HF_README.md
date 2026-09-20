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

This Hub repository currently contains the safety-calibrated v7 native-2M
candidate, distributed as a 4M-declared portable package. Its stable candidate
identity is `Wrench-4B-Qwen3.6-8E-Safety-v7-native2M`.

Wrench is a pruned, task-specific developer-tool SLM derived from Qwen3.6-35B-A3B.
It contains 3,881,244,016 parameters and stays below the 4.25B parameter ceiling.

This is a public experimental artifact. It is downloadable and reproducible, but it
is not a claim that the final 4M retrieval-quality or MiniMax-parity gates have
passed. The safety candidate is the better bounded-worker checkpoint found so
far, but it still requires a complete matched 220-case release evaluation.

## Copy the package

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M
```

The canonical distribution format is Hugging Face Safetensors. The package embeds
the tokenizer hook, deterministic mechanical lookup runtime, read-only verifier,
long-context overlay, hash-bound package metadata, and the FreeToken launcher. It
is intended to feel like one model directory, not a separately installed harness.

The bundled FreeToken launcher enables the package-local mechanical route for
high-confidence read-only proposals. Those requests return a standard chat
completion with `model_calls=0`; ambiguous requests continue through the model.
Every proposal remains subject to an independent verifier before execution.

The embedded worker API is available directly from the downloaded directory:

```python
from wrench_worker import WrenchWorker

worker = WrenchWorker.from_pretrained("./Wrench-4B-Qwen3.6-8E", load_model=False)
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

The bundled FreeToken launcher pins the 4M KV capacity explicitly and uses an
automatic expert cache. This avoids allocating an oversized sparse address
mapping on GPUs with limited memory. It improves the native serving profile,
but it does not by itself prove fast dense generation at 4M.

This endpoint is part of the downloaded package, not a separately installed
Wrench harness. It still does not claim dense native attention quality over
every 4M token. It provides the practical model-local path while that native
quality and throughput work continues.

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
experimental native profile. The bundled launcher selects native direct input,
pins a 4M KV capacity, and uses FreeToken's automatic expert cache with an 8K
reserve. The embedded worker's default fast path mechanically reduces noisy
payloads to a 64K effective working context. Native direct input and fast
staged input are recorded separately in receipts.

The embedded reducer has also passed a 4M mechanical stress diagnostic: 3,999,951
estimated raw tokens reduced to a 92-token model prefill, with 1.0 target-reference
recall, 1.0 current-intent preservation, and 1.0 hash-bound reference rate. The
measured cold ingest was 98.713 ms and hot selection was 44.441 ms on the local
development machine. This is deterministic toolbelt evidence, not an LLM
long-context quality or MiniMax-parity claim.

## Backend status

- Hugging Face Safetensors: public experimental package. Transformers 5.17.0+
  recognizes the bundled Qwen3.5 MoE architecture and Wrench tokenizer metadata.
- FreeToken: locally verified experimental backend.
- The bundled FreeToken path has produced a schema-valid read-only proposal on a
  small smoke request when given the explicit Wrench output contract.
- vLLM: requires a registered Wrench architecture adapter.
- Ollama, llama.cpp, and GGUF: not verified for Wrench hybrid attention and lookup
  semantics. Do not assume a generic GGUF conversion preserves these features.

## Known limits

The base checkpoint config is 2M position-capable. The 4M probe uses a runtime RoPE
extension and is not long-context training. Native 4M retrieval quality, throughput
under production concurrency, and the full MiniMax matched-workflow acceptance suite
remain open measurements.

The standard Transformers path has verified architecture/configuration,
tokenization, and full weight loading. Generation quality through plain
Transformers is not yet a pass and is intentionally not claimed here. Use the
bundled FreeToken profile for the current experimental generation path.

Wrench has no direct mutation authority. It proposes bounded developer-tool actions
or abstains; a surrounding verifier must enforce execution policy.
