# Phase 452: local retry token accounting

Date: 2026-09-24

## Change

The local Transformers worker could make a bounded repair generation after an
invalid model response. It reported the number of calls, but the workflow cost
receipt estimated prompt tokens from a single prefill or the raw request and
completion tokens from only the final response. This omitted the actual token
work from earlier local attempts.

The worker now records prompt token IDs and generated token IDs for each
completed generation attempt in a `wrench.local-model-usage-receipt.v1`. The
server validates those rows against the attempt count and aggregate totals,
then marks the source as `transformers_tokenizer_ids`. The existing estimate
remains the fallback for local-only results without this receipt. The
native-upstream path retains local accounting when it adds a frontier attempt;
the cost receipt reports local and frontier calls, repairs, and tokens
separately before summing workflow tokens.

## Evidence and limits

- Source inspection confirmed that each attempt's input batch and generated
  sequence are available in the local worker, and that the server receipt
  previously used only one prompt count and the final output estimate. It also
  confirmed the native-upstream path replaces the worker result after local
  inference, which previously discarded local counts.
- Static diff review and `git diff --check` completed. No tests, inference, or
  benchmark runs were performed.
- The receipt covers successful `generate()` attempts that return token IDs.
  It does not yet account for a generation call that raises before returning,
  and it does not establish verified task outcomes, provider dollar cost, or
  complete three-arm Gate D accounting. It reports upstream attempts with no
  usage row as `frontier_usage_missing_calls`; a usage row with malformed or
  unreconciled token values still needs separate validation. Local attempts
  lack stable request-scoped IDs in durable traces, and client-level corrective
  HTTP retries still retain only the final response's usage. The active Gate D
  scorer leaves net savings unscored. Gate D remains open.
