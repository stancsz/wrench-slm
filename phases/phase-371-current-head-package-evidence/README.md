# Phase 371: Current-Head Portable Package Evidence

Date: 2026-09-21

Status: `PASS_CURRENT_HEAD_HYBRID_PACKAGE_DIAGNOSTIC`

## Package binding

- Source HEAD at package materialization: `59b8b7c61639c3a9576af377eb6fe21067a39f98`
- Package: `D:\models\_wrench-release-candidate-59b8b7c`
- Source artifact: `_wrench-release-candidate-search-concurrent`
- Weight shards: `2`, hard-linked, no model load
- Package manifest SHA-256: `7a2e10dafa825c70a765ee031efcc6e78327a39659a029e37a125f08f28a3588`
- Package receipt SHA-256: `8c7fec6cddc4c874688d923295d41b01026f5ff322d55f5bd32fdd55b530046e`

## Verified hybrid route

Structural package validation and package mechanical smoke both passed. A
direct package-local OpenAI-compatible request accepted `4,000,000` requested
tokens, measured `3,999,995` estimated raw tokens, returned HTTP 200, and
completed in `276.011 ms`. The first-layer mechanical pruner/cherrypicker gate
completed in `24.587 ms`, bound the raw payload hash, retained the latest intent,
and exposed a `64,000` token working-context budget. The request used zero
model calls. This is model-local hybrid raw intake, not dense native attention.

The package retrieval probe passed all `6/6` cases at 2M and 4M placements
`1%`, `50%`, and `99%`, with zero model calls. Measured case latencies were
`15.442`, `16.882`, `20.733`, `25.425`, `37.583`, and `38.575 ms`.

## Client integration

The same package passed read-only client smoke for OpenCode and DeepSeek
Harness. Both exited `0`, observed structured reads, produced three trace
rows, used zero model calls, and claimed no mutation. Claude Code also
completed `Read README.md` through the local Anthropic Messages endpoint with
two trace rows, zero model calls, and a `3.051 ms` first-layer route. The
client's `MiniMax-M2.7` unrecognized-model warning remains recorded and did not
cause provider fallback.

## 220-case diagnostic replay

The same package completed the current v2 `220/220` replay with the captured
teacher trace input hash bound to
`da64a33d193389dc0ed47d564d86e1599e4d30c4ef425206af68fe991cd10a72`.

- Wrench plus identical MiniMax fallback: weighted final success `1.0`,
  verifier success `1.0`, frontier tokens `377`, local tokens `24,046`,
  fallback count `1`, p50/p95 `188.154/301.577 ms`, zero prohibited accepts,
  zero unexpected mutations.
- Wrench-only diagnostic: weighted final success `0.994936`, zero frontier
  tokens, zero prohibited accepts, zero unexpected mutations.
- MiniMax teacher-only: weighted final success `0.893420`, frontier tokens
  `74,450`, p50/p95 `3458.722/8180.346 ms`, and two prohibited accepts.
- The replay gates reported weighted mechanical frontier-token coverage `1.0`
  and net frontier-token savings `1.0`.

This is deterministic hybrid workflow evidence on a diagnostic historical
trace set. It is not learned MiniMax parity, dense-native 4M decoder quality,
independent RTX 5060 Ti evidence, or production approval.

## External receipt hashes

- 4M probe: `D:\models\wrench-phase-371-current-head-package\probe-4m.json`, SHA-256 `9d14b436c4adb93b7fe3ece048faed9cdab449ec6233bd891b8ff0d28e2a5564`
- Retrieval: `D:\models\wrench-phase-371-current-head-package\retrieval-2m-4m.json`, SHA-256 `f7c60fa9213749b2afa898a395732b3a1483ea0d2b665f3bea8793bb33b1f8a1`
- Client smoke: `D:\models\wrench-phase-371-current-head-package\clients\receipt.json`, SHA-256 `f6f7e93b2d5ee2ad4c1f3d98ec0b02751fedc9ce508759178cf6aee60b197bea`
- Claude trace: `D:\models\wrench-phase-371-current-head-package\claude\trace.jsonl`, SHA-256 `d9c7ce974d5e87ead2837827e3176a064feda692bf12d52d5219df3336d9282f`
- Replay evaluation: `D:\models\wrench-phase-371-current-head-package\replay-220\evaluation.json`, SHA-256 `979294c54f4e2ba7a7811aa9a9c1b10018067c854e29bc2ab95373c67d1e8fd7`
- Replay trace manifest: `D:\models\wrench-phase-371-current-head-package\replay-220\trace-manifest.json`, SHA-256 `b274e7830bc1189b15511abbd9b91177b4646415beae6d7cfa62a14658ffbb69`
