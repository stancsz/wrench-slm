# Wrench Qwen3.6 Expert-Tier Evaluation

Wrench's experimental specialized execution SLM targets narrowly defined,
independently verifiable developer-tool work. The project now evaluates two
per-layer router-selected candidates pruned from Qwen3.6-35B-A3B: an 8-expert
compact tier, a 16-expert practical tier, and a 32-expert expanded tier.

The compact BF16 checkpoint reports 3,881,244,016 actual parameters, the
practical 16-expert checkpoint reports 4,888,532,336, and the expanded
checkpoint reports 6,903,108,976. Their ideal INT4 weight-only estimates are
about 1.84 GiB, 2.32 GiB, and 3.28 GiB respectively. Real W4A16 NVFP4 exports
are currently about 4.02 GiB for 8 experts and 4.55 GiB for 16 experts. The
16-expert FTW artifact passed a bounded CUDA load and generation smoke. These
are experimental artifacts, not quality or production claims.

It may propose a bounded action or abstain. A separate verifier and router own
execution, fallback, accounting, circuit breaking, and rollback. The project is
not a general coding agent and has no autonomous-write authority.

The current investigation is whether either sparse candidate can be calibrated
for this narrow role. The identity, router profile, structural load, CUDA
forward path, and compact/practical packed export smokes are verified. The
artifacts are still experimental and uncalibrated: quality, performance,
production value, and release readiness are not established.

See [GOAL.md](GOAL.md) for the governing contract. The preserved pre-restart
implementation is outside this repository under
`C:\Users\stanc\github\portfolio\archives\wrench-slm-2026-09-17-pre-restart`.

The phased execution plan is in [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).
Phase evidence is kept under `phases/`; large local datasets remain outside Git.
