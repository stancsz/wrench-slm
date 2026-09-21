# Phase 295: current 220 repetition stability

To move the current replay toward Gate C's repetition requirement, the same
hash-bound current 220 suite was sent to the local MiniMax-compatible teacher
three complete times and replayed through the same current v103 package each
time. The complete repetitions are capture 1, capture 2, and capture 4. A
third attempted teacher capture had three transport failures and is retained
as a failed attempt, not silently repaired or included in the complete set.

All three complete teacher captures contain 220/220 responses, zero transport
failures, zero invalid responses, and the same current-suite hash
`da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`.

The package replay produced the following complete-run ranges:

| Arm | Weighted final success | Prohibited accepts | Wrench p50 | Wrench p95 |
| --- | ---: | ---: | ---: | ---: |
| Teacher-only | 0.8847288 to 0.8934198 | 2 to 4 | not applicable | not applicable |
| Wrench-only diagnostic | 1.0 in all three | 0 in all three | 189.286 to 199.715 ms | 302.501 to 315.719 ms |

The Wrench raw proposal for every case was byte-identical across all three
replays: 220/220 IDs matched with zero differing IDs. This is useful stability
evidence for the deterministic mechanical lane. It is still not a final Gate C
pass because the current suite remains a historical/calibration fixture, the
teacher identity is endpoint-recorded rather than independently bound, and
the approved family-disjoint real-workflow set, independent RTX 5060 Ti run,
and native learned-decoder quality are still open.

Hashes and external receipt paths are recorded in
`repetition-receipt.json`.
