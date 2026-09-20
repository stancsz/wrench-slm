# Phase 147: 4M native direct-input receipt

The package-server integration probe now exercises both explicit modes against
a local protocol stub.

## Evidence

- staged 4M mode: `PASS_NATIVE_HANDOFF_STAGED_4M`
- staged raw token estimate: `3,999,942`
- staged native prompt estimate: `1,845`
- staged server reduction: `85.714 ms` in the preceding optimized receipt
- direct 4M mode: `PASS_NATIVE_DIRECT_RAW_4M`
- direct raw token estimate: `3,999,942`
- direct upstream prompt tokens: `3,999,942`
- direct server staging: `0.0 ms`
- direct round trip: `2,747.084 ms`, including 35MB JSON construction and loopback I/O

The upstream is a protocol stub. These receipts prove mode separation, raw
intake, and token accounting only. They do not prove native dense attention,
retrieval quality, or generation quality.
