# Phase 194: v78 bundled package 220-case replay

Date: 2026-09-20

## Runtime

The v78 package was loaded from:

`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v78-bounded-verifier`

The package's own `wrench_runtime` server served the replay. Client mechanical
fast-path bypass was enabled, so every Wrench request went through the
package-local HTTP endpoint. The teacher arm reused the existing 220-case
MiniMax proposal capture and made no new provider request.

## Receipt

The corrected 220-case contract returned `PASS_MECHANICAL_WORKER`:

- 220 traces, 120 eligible mechanical traces;
- weighted mechanical frontier-token coverage: `90.9116%`;
- net frontier-token savings: `96.1611%`;
- Wrench-plus-identical-fallback weighted final success: `96.8925%`;
- teacher weighted final success: `68.9927%`;
- Wrench frontier tokens: `2,487` versus teacher `64,785` in this replay;
- Wrench local tokens: `23,643`;
- Wrench fallback count: `5`;
- zero prohibited accepts;
- zero unexpected mutations;
- Wrench-plus-fallback median latency: `199.148 ms`, p95 `1,987.271 ms`;
- Wrench-only diagnostic median latency: `198.711 ms`, p95 `394.225 ms`.

Evidence files are `evaluation.json` and `trace-manifest.json` in this phase.

## Limitation

This is still a historical diagnostic suite, not the final family-disjoint
approval. The current machine's live `localhost:4000` health service timed out
or returned oversized responses for several eligible health rows. The replay
therefore remains diagnostic until the same sealed contract is run against an
isolated deterministic health fixture. The verifier failed closed and recorded
the failures; no health behavior was weakened to improve the score.

The 5060Ti independent receipt is also still missing for the current source
commit. The private Drive queue contains an older pending job pinned to
`0d6546a`, not this package's source state.
