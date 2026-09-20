# Phase 122: native fast-history boundary repair

This phase fixes two bugs in the opt-in FreeToken native long-context path:

1. Dynamic `auto` history mode did not install its decoder patch because its
   parsed numeric boundary is intentionally zero.
2. A chunked FreeToken `Req` does not retain the complete prompt length. The
   overlay now carries `PendingReq.input_len` onto each chunk and computes the
   request-relative history boundary from that value.

## Evidence

`v38-native-3990k.json` records a direct request to FreeToken, with no Wrench
gateway reducer:

- requested target: 3,990,000 tokens
- provider prompt tokens: 3,995,331
- HTTP status: 200
- truncated: false
- native context pass: true
- elapsed: 173,384.564 ms
- configured model limit: 4,000,000 tokens

The serving logs also show old full chunks running through the skip path at
roughly 2.8M to 3.8M tokens per second, while the first and newest 64K tail
remain on the normal path. The end-to-end time is still minutes because the
newest 64K tail is intentionally quality-preserving full compute.

This proves native input capacity and the repaired fast-history execution path.
It does not prove retrieval quality, MiniMax parity, or production readiness.
