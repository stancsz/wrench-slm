# Wrench Qwen3.6 Expert-Tier Evaluation

Wrench's experimental specialized execution SLM targets narrowly defined,
independently verifiable developer-tool work. The project now evaluates two
per-layer router-selected candidates pruned from Qwen3.6-35B-A3B: an 8-expert
compact tier, a 16-expert practical tier, and a 32-expert expanded tier.

The compact BF16 checkpoint reports 3,881,244,016 actual parameters, the
practical 16-expert checkpoint reports 4,888,532,336, and the expanded
checkpoint reports 6,903,108,976. Their ideal INT4 weight-only estimates are
about 1.84 GiB, 2.32 GiB, and 3.28 GiB respectively. Text-only W4A16 NVFP4
FTW artifacts are 3.19 GiB for 8 experts and 3.72 GiB for 16 experts. Both
passed bounded CUDA load and generation smokes. These are experimental
artifacts, not quality or production claims.

It may propose a bounded action or abstain. A separate verifier and router own
execution, fallback, accounting, circuit breaking, and rollback. The project is
not a general coding agent and has no autonomous-write authority.

The current investigation is whether either sparse candidate can meet the
quality gate after calibration. A corrected synthetic holdout currently scores
both the 8-expert and 16-expert tiers 9/14 in BF16 and 7/14 after NVFP4
packing. Exact proposal-object matches are lower, at 6/14 for 8E BF16 and
4/14 for 16E BF16. These are development-only verifier receipts, not
production quality evidence.

The latest corrected calibration lineage now records hash-stable training
bytes and fresh packed receipts. On the separate 28-case unseen fixture, the
new 8E pack scored 9/28 exact proposal objects and the new 16E pack scored
7/28. The 8E artifact remains the smaller option; neither tier is production
enabled.

See [GOAL.md](GOAL.md) for the governing contract. The preserved pre-restart
implementation is outside this repository under
`C:\Users\stanc\github\portfolio\archives\wrench-slm-2026-09-17-pre-restart`.

The phased execution plan is in [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).
Phase evidence is kept under `phases/`; large local datasets remain outside Git.
