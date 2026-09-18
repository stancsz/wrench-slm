# Wrench Qwen3.6 Expert-Tier Evaluation

Wrench's experimental specialized execution SLM targets narrowly defined,
independently verifiable developer-tool work. The project evaluates an
8-expert compact tier and a 16-expert larger tier pruned from Qwen3.6-35B-A3B.
The 32-expert path remains an optional BF16 structural experiment.

The compact BF16 checkpoint reports 3,881,244,016 actual parameters and the
16-expert checkpoint reports 4,888,532,336. Their ideal INT4 weight-only
estimates are about 1.81 GiB and 2.28 GiB. Actual text-only W4A16 NVFP4
artifacts are 3.188 GiB for 8 experts and 3.718 GiB for 16 experts. Both
passed bounded CUDA load and generation smokes. These are experimental
artifacts, not quality or production claims.

It may propose a bounded action or abstain. A separate verifier and router own
execution, fallback, accounting, circuit breaking, and rollback. The project is
not a general coding agent and has no autonomous-write authority.

The current guarded broad fixture scores the 8E tier 11/28 accepted and 19/28
expected outcomes, and the 16E tier 14/28 accepted and 22/28 expected
outcomes. Both have zero prohibited accepts after intent guards. These are
development-only verifier receipts, not production quality evidence.

The latest calibration lineage records hash-stable training bytes and fresh
packed receipts. The 16E tier is the current more-useful experimental
candidate; the 8E tier remains the smaller and faster option. Neither tier is
production enabled.

The original 35B teacher baseline scored 12/28 verifier outcomes and 7/28
exact proposals after a receipt-visible generic-tool schema adapter. The
adapter is baseline-only and is not part of Wrench runtime.

See [GOAL.md](GOAL.md) for the governing contract. The preserved pre-restart
implementation is outside this repository under
`C:\Users\stanc\github\portfolio\archives\wrench-slm-2026-09-17-pre-restart`.

The phased execution plan is in [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).
See [docs/WRENCH_MODEL_TIERS.md](docs/WRENCH_MODEL_TIERS.md) for current paths,
selection guidance, and measured guarded comparisons.
Phase evidence is kept under `phases/`; large local datasets remain outside Git.
