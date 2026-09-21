# Phase 290: complete dispatch payload and fresh local validation

This phase records the first complete self-contained worker payload after the
remote thread repeatedly returned empty turns. The dispatch contract now says
that every job must repeat its objective, source and artifact identity,
resource reserve, allowed commands, stop conditions, and final response schema.
An empty turn or wrong-host execution is unverified and must not be repaired by
appending more context to the same thread.

The local source regression passed 194 tests with 18 deprecation warnings. On
the RTX 5070 Ti, the current v103 package accepted the direct 4M package-local
route in 156.5 ms for 31,997,963 raw characters. The six-case 2M/4M retrieval
probe passed with zero model calls. Three package-only 220-case repetitions
each produced 220/220 outcome matches, 120/120 exact proposals, zero
prohibited accepts, zero model calls, and p50/p95 latencies of
0.528/38.883 ms, 0.531/40.814 ms, and 0.503/39.670 ms.

These results are diagnostic package evidence only. They do not prove
MiniMax parity, family-disjoint approval, production enablement, or RTX 5060
Ti performance. The clean new task ran on the local RTX 5070 Ti, and handoff
to the 5060Ti host failed because no matching saved project exists there.
