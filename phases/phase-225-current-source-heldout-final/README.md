# Phase 225: current-source held-out final diagnostic

The checked-out source endpoint was replayed against the sealed v2 `final.jsonl` split with the client mechanical fast path enabled and the deterministic health fixture isolated on loopback port 28907.

Result:

- 44/44 overall outcome matches
- 24/24 eligible exact accepts
- 0 prohibited accepts
- 0 transport or runtime abstentions
- 44/44 mechanical fast-path requests
- 0 model calls
- median latency 0.528 ms
- p95 latency 45.774 ms

This is stronger held-out regression evidence than the earlier host-dependent
43/44 receipt. It is still a diagnostic, not a MiniMax parity or production
approval result. The split is 44 rows and does not establish the required
weighted workflow coverage, teacher-only comparison, independent 5060 Ti
verification, or dense-native attention quality.

The fixture correction used by the runner binds the test health endpoints to a
dedicated IPv4 loopback port and restores the environment after the run. It
does not change production health transport behavior.
