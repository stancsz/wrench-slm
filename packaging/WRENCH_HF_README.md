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

Wrench is a bounded developer-tool execution SLM for fast, repetitive,
verifiable mechanical work. It proposes structured actions or abstains. An
independent verifier and the stronger-model fallback retain final authority.
Wrench never executes arbitrary shell commands, uses credentials, or writes
autonomously.

This experimental candidate is derived from Qwen3.6-35B-A3B, uses NVFP4 W4A16
weights, and contains `3,881,244,016` verified parameters, below the 4.25B
parameter ceiling. It is not a general coding agent.

## Copy the package

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M `
  --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M
Set-Location Wrench-4B-Qwen3.6-8E-NVFP4-native4M
.\run_wrench.ps1
```

The package is a Hugging Face Safetensors directory with tokenizer, bundled
verifier, deterministic toolbelt, context policy, and a model-local server.
It accepts Ollama-shaped `/api/chat` and `/api/generate` requests, including
`options.num_ctx=4000000`, without an external gateway.

## What the 4M claim means

The production-value path is hybrid and model-local:

1. receive the complete raw payload directly at the package endpoint;
2. use deterministic MapReduce, bounded search, AST/dependency extraction,
   and exact lookup windows to identify useful evidence;
3. keep recent intent hot and old material reference-only;
4. compact model work to a bounded effective context, normally 64K;
5. run the bounded proposal, verifier, and identical stronger-model fallback.

The first-layer receipt records selected and omitted spans, raw payload hash,
effective working context, route source, and gate latency. Dense native 2M/4M
attention is optional research. It is not the Wrench product claim.

When the optional dense-native lane is enabled, use the bundled launcher with
`-DenseNativeGate`. The raw request still arrives at the model-local native
endpoint, but the package's first model-side stage compacts it to 32K to 64K
before expensive attention:

```powershell
.\serve_freetoken.ps1 -OllamaApi -NativeDirectInput -DenseNativeGate
```

The gate is fail-closed and records the raw payload hash, selected working
context, and gate stage. Omitting `-DenseNativeGate` is reserved for separate
reducer-bypassed native capacity probes, not the dense-native product path.

## Run the model-local endpoint

```powershell
python .\wrench_server.py --model-dir . --allowed-root . --mechanical-only
```

The endpoint is `http://127.0.0.1:28900/v1/chat/completions`. The same process
also exposes `/api/tags`, `/api/show`, `/api/chat`, and `/api/generate` for
clients that expect an Ollama-shaped surface. It receives the full raw
conversation directly and emits hash-bound context-gate receipts.

The `--mechanical-only` mode is the verified fast path. Remove it only when a
compatible local native backend is available for ambiguous requests. Native
generation is separately verified and must not be inferred from the API shape.

The embedded worker API is also available directly from the downloaded
directory:

```python
from wrench_worker import WrenchWorker

worker = WrenchWorker.from_pretrained(
    "./Wrench-4B-Qwen3.6-8E-NVFP4-native4M", load_model=False
)
result = worker.propose([
    {"role": "user", "content": "Read README.md with a 65536 byte limit."}
])
```

## Current evidence

On the historical 220-case diagnostic replay, with client-side mechanical
shortcut disabled:

- weighted mechanical frontier-token coverage: `94.5411%`;
- net frontier-token savings: `95.5310%`;
- Wrench plus identical MiniMax fallback final success: `99.6503%`;
- median / p95 latency: `183.314 ms` / `337.174 ms`;
- prohibited accepts: `0`;
- unexpected mutations: `0`.

The direct model-local context matrix passed three repetitions each at 64K,
128K, 256K, 2M, and 4M. At 4M, the measured raw estimate was `3,999,995`
tokens and complete HTTP p50/p95 was `158.906` / `159.251 ms`. The 2M/4M
reference-lookup probe recovered exact proposals in `18/18` cases, with 4M
retrieval p50/p95 of `32.560` / `40.772 ms` and zero model calls.

These are hybrid model-local diagnostics, not dense native attention quality,
stock Ollama native generation quality, family-disjoint approval, or
production enablement. The current stock Ollama native generation boundary is
explicitly recorded as failed on the validation host. GGUF and vLLM require
architecture adapters and are not claimed as verified.

## Development status

The full source regression is `168 passed`. Final release still requires the
human-approved family-disjoint MiniMax-worker trace set, independent RTX 5060
Ti verification, and operational shadow evidence. Wrench has no direct
mutation authority. It proposes bounded actions or abstains, and the
surrounding verifier must enforce execution policy.
