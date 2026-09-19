# Phase 70: mechanical 4M to 64K map-reduce

Status: `IMPLEMENTED_TESTED_HOT_PATH_PROVISIONAL`

This phase adds a content-addressed `MechanicalPrefillIndex`. Regex anchors,
symbol/error/path/test extraction, token counts, and normalized hashes are
computed once as context arrives. A later request reuses those cards and only
does query-term scoring, recency ordering, deduplication, and bounded rendering.
No LLM is used in this map-reduce stage.

## Measured synthetic stress

The benchmark used 64 distinct mechanical reference messages, each 75,000
word-estimate tokens, plus a current intent. The raw payload was 4,000,013
word-estimate tokens. Under the earlier 40K profile, the cached reducer
produced 14,879 model-prefill tokens, 64 reference cards, and a 4.826 ms hot
selection time on the local Windows workstation. The production default is now
a 64K effective working context: 48K recent hot context plus up to 16K
mechanical reference cards. Cold indexing took 5,850.252 ms and is intentionally
excluded from the hot request SLA because it runs incrementally during ingestion.

This is a mechanical compression benchmark, not model-quality evidence. The
cards retain hashes and high-value anchors while the original message bodies
remain available through the read-only lookup table. A realistic corpus must
still validate recall, false omission, injection handling, and final worker
success on family-disjoint traces.

## Boundary

The 100 ms target applies to cached 4M-to-64K working-set selection. It does not
claim that a 4B model can perform a fresh 4M-token attention prefill in 100 ms.
The serving receipt must report raw input tokens, model-prefill tokens, cold
ingest time, hot selection time, model prefill time, and lookup expansions
separately.

## Runtime integration evidence

The FreeToken Wrench profile now runs the reducer inside the serving submission
path. A real 4M-configured endpoint accepted a synthetic raw input estimate of
4,000,023 tokens and sent 1,278 exact engine prompt tokens to the model. The
mechanical ingest was 123.772 ms and hot selection was 0.245 ms. This proves
the 64K staged serving path, but it is not a native 4M attention pass or a
quality result. The receipt is `runtime-4m-64k.json`.
