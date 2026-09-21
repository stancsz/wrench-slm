# Phase 293: current 220 teacher-aligned replay

The current `evals/wrench-expanded-v2/cases.jsonl` fixture was captured again
against the local MiniMax-compatible teacher at `127.0.0.1:4000`. This was
necessary because the current fixture is not byte- or prompt-identical to the
older phase-185 capture: several read byte ceilings changed from 131072 to
262144 and the out-of-domain rows changed.

The new teacher capture contains 220/220 responses, zero transport failures,
and zero invalid responses. Its canonical and raw input hash is
`da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`, exactly
matching the current cases file.

The current v103 materialized package then completed the package replay across
teacher-only, rules-plus-fallback, Wrench-plus-fallback, and Wrench-only
diagnostic arms. The 220-row fixture contains 120 eligible rows. Wrench's
deterministic lane reached weighted final success `1.0`, weighted verifier
success `1.0`, zero prohibited accepts, zero unexpected mutations, zero
frontier teacher tokens, 24141 local tokens, median latency `193.818 ms`, and
p95 latency `315.719 ms`. The teacher-only arm reached weighted final success
`0.8934198331788693`, had two prohibited accepts, used `37544` weighted
frontier tokens, median latency `3458.722 ms`, and p95 latency `8180.346 ms`.

These numbers support the bounded mechanical-worker direction and the token
saving hypothesis on this fixture. They do not authorize a production claim:
the suite is still historical/calibration data, not the approved
family-disjoint real-workflow trace set; the teacher identity is only
endpoint-recorded; and native learned-decoder quality, sustained concurrency,
independent RTX 5060 Ti execution, and MiniMax semantic parity remain open.

Raw teacher and replay receipts remain in the external temporary paths listed
in `current-220-replay-receipt.json`.
