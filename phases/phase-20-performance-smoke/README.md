# Phase 20: bounded local performance smoke

This phase measures one real request through the local Qwen adapter using a
monotonic wall-clock timer and the server-reported token usage. A first loose
prompt correctly abstained because Qwen returned non-JSON; the exact-schema
retry then passed. Both attempts are preserved in the receipt.

The output is diagnostic only. It is not a throughput benchmark, a p95 or p99
measurement, a quality result, or evidence that the target under-4B model
exists.
