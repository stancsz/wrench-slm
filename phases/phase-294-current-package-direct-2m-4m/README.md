# Phase 294: current package direct 2M/4M intake

The current materialized package `D:\models\_wrench-current-client-20260921`
was probed through its model-local HTTP server, without an API gateway or
external summarizer.

The 2M probe delivered `1,999,998` prompt tokens to the package endpoint and
returned HTTP 200. The package accepted the request through the embedded
mechanical route, bound the raw payload hash, kept the effective working
context at 9 tokens for this exact lookup, and completed the package-server
portion in `21.957 ms` with zero model calls.

The 4M probe delivered `3,999,995` prompt tokens and returned HTTP 200. It
likewise preserved the raw payload hash, compacted to a 64K working budget,
and completed the package-server portion in `51.020 ms` with zero model calls.
The end-to-end probe timings, which include starting and stopping the local
server, were `86.537 ms` for 2M and `171.869 ms` for 4M. The server-side gate
timing is the relevant warm-process measure.

This is direct package intake plus deterministic MapReduce/pruner/cherrypicker
evidence. It is not a claim that dense full-attention native decoding over 4M
tokens is high quality. The native learned lane remains separately
diagnostic-only, while the fast mechanical lane is the production-value path.

The exact probe receipts and hashes are recorded in
`direct-context-receipt.json`.
