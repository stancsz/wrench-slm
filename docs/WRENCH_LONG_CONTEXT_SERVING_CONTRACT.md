# Wrench Native Long-Context Serving Contract

Status: experimental architecture contract

## Product requirement

Wrench must be a normal model artifact that can be loaded by a standard model
runtime and must accept a sequence of up to 4,000,000 tokens directly at the
model serving endpoint. This is the same class of requirement as an Ollama
model configured with `num_ctx=4000000` or a vLLM model configured with
`max_model_len=4000000`.

A gateway, context ledger, AST, retrieval index, summary, or preselector may
help manage the payload, but none of those count as native 2M support if they
silently remove tokens before the model receives the request.

## Required serving shape

```text
direct request containing up to 4M tokens
    -> tokenizer in the selected serving runtime
    -> Wrench model with native max context >= 2M
    -> long-context attention/state/cache implementation
    -> bounded proposal or explicit abstention
    -> independent proposal verifier
```

An optional gateway or context ledger may sit in front of this path for cache
reuse, audit, and retrieval. It is an optimization and observability layer,
not the native-context implementation:

```text
optional raw payload and cache/index layer
    -> direct model request, still allowed to contain the full 2M sequence
```

## Recency-first behavior inside a native 4M request

Most long payloads are expected to contain stale conversation, repeated
observations, old lookups, or historical artifacts. The model and runtime may
use an explicit retention policy:

```text
hot: recent user intent, recent tool state, unresolved dependencies
warm: recent summaries and task-linked working history
reference: old lookups, old logs, old file snapshots, completed tool results
cold: immutable payload retained for audit or on-demand retrieval
```

Old lookups are reference-only by default. A retrieval or cache policy may
promote a bounded span into the active working set, but the direct 4M serving
test must also prove that the model can receive the full sequence without
gateway truncation. Selective attention is acceptable. Selective intake that
changes the model input length is not a substitute for this gate.

The current intent must be represented separately from the historical lookup
material. The serving stack should make the newest user intent, unresolved
dependencies, and latest tool observations easy for the model to access. Old
material can act as test-time lookup evidence. This is why 2M is useful even
when only a small fraction of the sequence deserves active attention.

Four million tokens is the release target for this project. Two million is an
intermediate milestone. A larger declared limit without direct model-side token
evidence is not a pass.

## Artifact contract

The selected Wrench candidate must have a standard Hugging Face-style artifact:

- `config.json` with an architecture supported by the selected runtime;
- indexed Safetensors weights and tokenizer files;
- generation and chat-template metadata;
- explicit native context and positional parameters;
- model, tokenizer, runtime, and verifier hashes in the serving manifest.

FreeToken `.ftw` packages remain experimental backend artifacts. They are not
the canonical model package for vLLM or Ollama compatibility.

## Runtime and model strategy

vLLM is the primary serving target. Ollama is a required compatibility target
when the exported architecture is supported by its backend. Both paths must
load the same model lineage and must expose their configured maximum context.

Native 4M support requires more than changing a config integer. The candidate
must demonstrate compatible positional scaling or long-context training,
long-sequence kernels, cache management, chunked prefill, and quality
validation. A hybrid linear or recurrent-style attention path can reduce the
cost of old context, but it does not remove the need to measure the actual
model-visible sequence length.

The runtime may use GPU, CPU, or tiered cache when memory supports it. It must
report the allocation and fail closed on OOM or timeout. It must not claim a
successful 4M request after silently truncating, summarizing, or dropping the
oldest tokens.

## Safety and observability invariants

- System, developer, safety, authority, active task, and required dependency
  context cannot be silently dropped.
- Every optional selected or omitted span has a hash-bound receipt and source
  offset.
- Tool-call and tool-result units remain atomic.
- Low-confidence selection abstains or preserves the original request for
  frontier fallback.
- OOM, timeout, parser, cache, and runtime failures fail closed.
- The serving receipt records requested tokens, tokenizer identity, actual
  `prompt_tokens`, configured max context, truncation status, prefill latency,
  decode latency, peak memory, cache tier, cache hit rate, and fallback state.

## Native 4M acceptance gates

The contract is not complete until all of the following are measured:

1. A standard Safetensors artifact loads through vLLM and produces a verified
   bounded proposal.
2. The same artifact, or an explicitly documented compatible conversion, loads
   through Ollama without silently changing the tokenizer or tool contract.
3. A direct request to each claimed runtime contains a 4,000,000-token input,
   reports actual model-side `prompt_tokens` at or above the frozen tolerance,
   and proves no truncation or gateway compaction occurred.
4. Native long-context recall and end-to-end task success are measured with
   needles and mechanical tasks near the beginning, middle, and end of the
   4M sequence, including mostly irrelevant history and reference-only old
   lookups.
5. Prefill, decode, end-to-end latency, throughput, peak memory, cache hit
   rate, and concurrency are measured at representative shorter lengths and
   at the 4M stress point where hardware permits.
6. Insufficient-memory requests compact or fall back cleanly, while a request
   that passes the 2M gate never relies on an OOM crash as control flow.

Until these gates pass, the correct status is experimental, not native 2M
production support.
