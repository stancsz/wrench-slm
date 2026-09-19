# Phase 71: native attention and retrieval quality

Status: `RETRIEVAL_DIAGNOSTIC_PASS_NATIVE_1M_IN_PROGRESS`

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
