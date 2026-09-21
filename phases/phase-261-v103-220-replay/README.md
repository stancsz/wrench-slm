# Phase 261: v103 package 220-case replay

Status: `PASS_MECHANICAL_WORKER` on the current RTX 5070 Ti host.

This replay sends all 220 cases through the current v103 package-local HTTP
server using `tools/run_package_220_replay.py`. The evaluator client
mechanical shortcut was disabled. No decoder generation or additional VRAM
allocation was requested.

## Result

The `wrench_plus_identical_minimax_fallback` arm recorded:

- weighted final success: `0.9965032764`
- weighted verifier success: `1.0`
- weighted mechanical frontier-token coverage: `0.9929861390`
- net frontier-token savings: `1.0`
- frontier tokens: `0`
- local tokens: `24,141`
- fallback count: `0`
- median latency: `184.360 ms`
- p95 latency: `294.950 ms`
- prohibited accepts: `0`
- unexpected mutations: `0`

All five diagnostic evaluator gates are true. The Wrench-only diagnostic arm
has the same final success and safety result on this fixture, with no
frontier fallback.

This is strong evidence for the current package's bounded mechanical-worker
lane across all 220 fixture cases. It remains diagnostic rather than a
production authorization because the fixture is historical, the teacher
capture is proposal-only, dense-native decoder quality is not proven, and the
independent RTX 5060 Ti run is still pending.

Evidence:

- `evaluation.json`
- `trace-manifest.json`
- `../phase-253-v102-220-replay/README.md` for the previous package comparison
