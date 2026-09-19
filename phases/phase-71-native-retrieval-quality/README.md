# Phase 71: native attention and retrieval quality

Status: `RETRIEVAL_DIAGNOSTIC_PASS_NATIVE_1M_PERFORMANCE_FAIL`

This phase separates two claims that must not be conflated:

1. the model endpoint can receive a million-token payload and report exact
   model-side prompt accounting without the Wrench gateway compacting it;
2. deterministic retrieval can recover old reference material while preserving
   the newest intent and authority boundaries.

The retrieval check uses 220 cold-reference cases with unique paths, symbols,
errors, and current intents. It calls no LLM. Its receipt is
`retrieval-220.json`.

The native attention probe is run against the long-context model endpoint with
the Wrench reducer bypassed. A successful receipt must bind the tokenizer,
requested target, actual prompt tokens, no-truncation state, endpoint model,
and latency. A reducer receipt or an API gateway receipt is not sufficient.

Current evidence: the 220-case deterministic retrieval diagnostic passes with
1.0 target-reference recall, 1.0 current-intent preservation, and 1.0
hash-bound reference rate. The reducer-bypassed 1M native probe was stopped
after 567 seconds without an HTTP response while GPU work remained saturated.
Therefore native 1M attention is not a release claim. The supported fast path
is 4M raw input reduced mechanically to a verified 64K effective working
context, with no model call in the lookup stage.
