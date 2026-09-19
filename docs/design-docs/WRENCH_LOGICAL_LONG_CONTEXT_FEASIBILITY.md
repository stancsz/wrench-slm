# Wrench logical long-context feasibility

Status: proposed architecture note, not implementation or release evidence.
Updated: 2026-09-19

## Decision summary

Wrench can support a 1 to 2 million token **logical context** and still feel
fast if the system stores the full session outside the model and gives each
model call a small, task-specific working set.

The current Wrench model and runtime should not be described as natively
supporting 1 to 2 million tokens. Full attention over the entire window would
make prefill expensive, make the KV cache too large for the current local
hardware target, and create a quality risk that position-extension tricks do
not solve by themselves.

The product boundary should therefore be:

> Wrench retains up to 2M logical tokens, retrieves and verifies the relevant
> context, and sends a bounded active context to the local model or fallback
> model.

## Evidence from the current repository

- `src/wrench_harness/client.py` sends one bounded chat-completion request and
  limits generated output to 512 tokens. It does not implement a context
  ledger, retrieval, summarization, or input-token budget.
- `src/wrench_harness/router.py` bounds attempts and opens a circuit after
  failures, but it has no context admission, cache, or compaction state.
- The current shadow receipt used a 114-token prompt. It proves one local
  proposal passed the verifier, not long-context behavior.
- The active production contract explicitly requires context compaction and
  fallback work to be included in token, cost, and latency accounting.

This means the target is an architectural extension, not a configuration
change to the existing proposal client.

## Why native 2M full attention is not the fast path

For a decoder transformer, the approximate KV-cache footprint is:

```text
bytes per token = 2 * layers * KV heads * head dimension * bytes per value
```

The factor of two accounts for keys and values. For illustration, a model
with 32 layers, 8 KV heads, head dimension 128, and BF16 values would need
about 128 KiB of KV cache per token, or roughly 244 GiB for 2M tokens. The
actual number depends on the model's layer count, grouped-query layout, head
dimension, and cache precision, but the order of magnitude is the important
constraint.

Prefill attention also grows approximately quadratically with sequence length.
Moving from 1M to 2M tokens therefore multiplies full-prefill attention work
by about four. Decode still has to read a very large cache for every new
token. Sparse attention, recurrent state, or a purpose-built long-context
model can change this tradeoff, but they require a different model/runtime
design and must be measured rather than inferred from the advertised window.

## Recommended architecture

```text
session input
    -> immutable segments with IDs, hashes, token counts, and source order
    -> hierarchical summaries at session, task, file, and segment levels
    -> hybrid retrieval: exact match, metadata, recency, and embeddings
    -> context planner with a hard active-token budget
    -> prompt assembler preserving instructions, tool units, and latest task
    -> Wrench proposal model or stronger fallback
    -> verifier and context receipt
```

The context planner must preserve complete tool-call/result units and the
current task contract. It may remove or summarize old material only when the
result remains traceable to source segment IDs. Unsupported opaque state must
cause fallback, not silent deletion.

The ledger now supports derived summary segments. A summary records the source
segment IDs it represents and consumes active request budget when selected, but
does not double-count the original source tokens against the logical session
ceiling. Summary creation remains an upstream responsibility until a trusted
summarizer is independently evaluated.

The main performance levers are:

1. Index and summarize once when context arrives, rather than on every query.
2. Keep a small recent raw window plus a task-specific retrieved window.
3. Cache stable prefixes and hot retrieved segments.
4. Use exact search and metadata filters before expensive embedding work.
5. Run Wrench only when the selected context is inside its approved task
   family; otherwise preserve the original request and fall back.
6. Account for indexing, retrieval, summarization, verification, retries, and
   fallback in the complete workflow measurement.

## Current request-path slice

`execute_local_qwen` now accepts an optional `ContextLedger`. When supplied, it
forwards only system/developer instructions, one bounded retrieved-context
message, and the latest user request. The previous full message history is not
forwarded. The context receipt is returned with the verifier result, and the
client defaults to a compact omission summary while allowing a full audit
receipt.

This is still a provider-free integration proof. It does not establish that a
model can answer correctly from retrieved context, and it does not authorize
learned routing or production enablement.

## Proposed acceptance boundary

The first implementation goal should be a logical-context goal, not a native
2M-attention goal:

- Ingest and address 1M and 2M-token sessions without duplicate, reordered, or
  silently dropped segments.
- Produce a context receipt containing session hash, segment IDs, source order,
  token counts, selected segments, summaries, and omitted-segment reasons.
- Preserve system/developer instructions, the latest user request, active tool
  pairs, and safety-relevant observations across compaction.
- Measure needle-in-context, recency, conflict, tool-continuity, prompt
  injection, and unsupported-opaque-state cases.
- Measure cold and warm latency separately on the named 5070 Ti and 5060 Ti
  hosts. Report time spent in ingestion, indexing, retrieval, assembly,
  generation, verification, and fallback.
- Include context-management overhead in the existing three-arm workflow
  accounting. A lower provider token count alone is not a pass.
- Keep provider outbound ceilings explicit. A 2M logical Wrench session does
  not imply a 2M-token provider request.

## What would count as native 2M support

Native support would require a separately verified model/runtime path using
one or more of sparse or block attention, recurrent or state-space memory,
distributed/ring attention, aggressive KV-cache quantization, or a model
trained for the extended positional regime. It would need independent tests
for long-range retrieval, position bias, lost-in-the-middle behavior,
prefill/decode latency, cache memory, concurrency, and failure recovery.

RoPE scaling or increasing a configuration field is not enough evidence.

## Current verdict

**Feasible:** 1 to 2M logical context with bounded active attention, caching,
retrieval, and fallback.

**Not credible as a fast local claim:** native full-attention 1 to 2M context
on the current small Wrench model and workstation target.

**Next proof:** build a no-provider context ledger and replay benchmark first,
then connect it to the existing verifier path. Do not change the release gates
or enable learned routing until the complete workflow evidence passes them.
