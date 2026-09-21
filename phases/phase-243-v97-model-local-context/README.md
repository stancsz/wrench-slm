# Phase 243: v97 model-local 2M and 4M context probe

This phase exercises the published v97 package itself through its bundled
`/v1/chat/completions` server. It does not use the API gateway and does not
load a dense decoder. The package receives the full raw payload, performs its
first-layer deterministic pruner and cherrypicker, and returns a bounded
mechanical proposal.

Results on the local development host:

- 2,000,000 estimated input tokens: HTTP 200, `102.565 ms`, zero model calls.
- 4,000,000 estimated input tokens: HTTP 200, `187.113 ms`, zero model calls.
- The 4M receipt records `3,999,995` prompt tokens, a hash-bound raw payload,
  `mechanical_fast_pruner_cherrypicker`, and a 64K working-context budget.
- The accepted action was a bounded `read_file` proposal. This proves the
  model-local mechanical context path, not dense native attention quality or
  MiniMax parity.

Receipts:

- `v97-2m.json`
- `v97-4m.json`
