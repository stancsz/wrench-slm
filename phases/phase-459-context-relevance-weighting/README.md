# Phase 459: reduce common-word bias in context retrieval

Date: 2026-09-23

## Change

Context retrieval now filters common English stopwords, treats repeated query
terms as a single signal, and weights remaining term matches by inverse
document frequency. Scoring occurs per atomic unit, so repeating one term
across several members of a call/result unit does not boost that unit. IDF is
computed over the same eligible atomic-unit corpus used for selection, so
cold-only and mixed-cold units cannot perturb eligible rankings. Terms are
processed in sorted order to keep accumulation deterministic.

## Verification

- `python -m pytest tests/test_context.py tests/test_context_client.py -q`:
  26 passed in 4.38 seconds.
- New regressions show a distinctive `verifier` match wins over three
  `deployment` matches when the query repeats `deployment`, common `the`
  tokens do not displace the distinctive result, and duplicate matches across
  a larger call/result unit do not win by member count alone. An added
  metamorphic case confirms that adding cold-only or mixed-cold query matches
  leaves eligible-unit ranking unchanged.
- `python -m ruff check src/wrench_harness/context.py tests/test_context.py`:
  passed.

## Limits

This verifies ranking mechanics on focused fixtures. It does not measure
retrieval quality on representative Wrench workflows, bound the full prompt
including framing, or establish production utility. No model inference,
provider request, or real-workflow replay was run.
