# Phase 63: provider-free logical-context ledger

This phase adds `wrench_harness.context.ContextLedger` and a deterministic
benchmark for the first architectural slice of the 1M to 2M logical-context
proposal.

The ledger provides:

- hash-bound segments with explicit source order and token counts;
- a configurable logical admission ceiling, tested at 2,000,000 tokens;
- one-time lexical indexing and query retrieval;
- bounded active-context assembly;
- atomic tool-call/result units;
- explicit omitted-segment reasons; and
- receipts that distinguish logical-context mechanics from model evidence.

The benchmark does not call a provider or model. Its explicit token counts are
logical accounting values, so this phase does not establish native 2M attention,
quality, provider latency, cost savings, or production readiness.

## Latest local receipt

`benchmark.json` was generated with 20,000 segments at 100 logical tokens each,
for a 2,000,000-token ledger and a 4,000-token active budget. On the current
Windows host, the latest receipt measured 158.276 ms ingestion and indexing,
0.061 ms indexed search, 93.666 ms cold session hashing, and 64.597 ms warm
bounded assembly and compact receipt creation. These are point-in-time
provider-free mechanics measurements, not a hardware-independent speed
guarantee.

The materialized companion receipt `benchmark-materialized.json` indexed actual
word-token-like segment text totaling 2,000,000 estimated words. It measured
975.522 ms ingestion and indexing, 0.064 ms indexed search, 197.115 ms cold
session hashing, and 64.653 ms warm bounded assembly. The word estimate is not
the Qwen tokenizer, so this remains a storage and retrieval measurement rather
than model-context evidence.
