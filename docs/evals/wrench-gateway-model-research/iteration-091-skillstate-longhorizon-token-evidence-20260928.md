# Iteration 091: structured execution state and long-horizon token evidence

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-EVAL-ITER091-SKILLSTATE-LONGHORIZON-PROOF-20260928`

Status: **high-value external evidence found; Wrench proof still required**

Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`

Gateway research goal SHA-256 preserved:
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Finding

The closest evidence to the 95% target is not generic text compression. In
[SKILL.state](https://arxiv.org/abs/2608.26263), the runtime discards prior
reasoning/action transcripts after each validated transition and supplies the
model with an immutable task specification, bounded structured execution state,
and the latest observation. State is merged and validated deterministically;
history can remain outside the prompt for audit and retrieval.

In the paper's 100-step simulated software-repository environment, cumulative
tokens fell from 1,848,500 for the transcript/ReAct runtime to 90,200 for
SKILL.state, a **95.12% reduction**. The action-resolution score rose from
0.53 to 0.78. Savings depended strongly on horizon: 34.8% at 10 steps, 80.4%
at 25, 90.2% at 50, and 95.1% at 100. A short-task-heavy workload would not
inherit the 100-step result unchanged.

| Simulated repository horizon | ReAct score | State score | ReAct tokens | State tokens | Token reduction |
|---:|---:|---:|---:|---:|---:|
| 10 steps | 0.89 | 1.00 | 11,670 | 7,608 | 34.8% |
| 25 steps | 0.84 | 0.88 | 111,970 | 21,920 | 80.4% |
| 50 steps | 0.71 | 0.86 | 462,118 | 45,100 | 90.2% |
| 100 steps | 0.53 | 0.78 | 1,848,500 | 90,200 | 95.1% |

This is promising architecture evidence, not a Wrench result. The software
repository task is a deterministic simulation of branch/PR/CI state and
procedural actions; it does not patch and test real repositories. Its long
horizon score is the fraction of actions resolved correctly, not a measured
SWE-bench issue-resolution rate. The 100-step evidence uses Gemini-3-Flash,
not Wrench's local LoRA. The paper's public interactive benchmarks show more
modest savings: 60.4% on InterCode CTF, 22.5% on τ-Bench Retail, and 40.6% on
τ-Bench Airline, alongside reported success gains. The open-weight Qwen3-8B
result is on the synthetic warehouse task, not the software-repository
environment, and is not a Qwen3.5-4B LoRA result.

The paper also supplies a concrete failure warning: the sufficient-state
assumption fails when the needed schema is unknown, when a previously observed
fact was not captured in state, or when the task itself requires explaining
the historical trajectory. Its open-weight model analysis finds state-patch
overwrite/deletion, type, and JSON-format errors. For Wrench, this argues for
versioned state patches with required-field and provenance checks, deterministic
merge/rollback, raw observations retained outside prompt context, and
hash-addressed fetch-on-demand for details. A free-form summary cannot replace
that evidence store.

## Implication for Wrench's next experiment

Treat structured state as the main 95% token-saving hypothesis. Keep the LoRA
requirement by training the local controller to propose bounded state patches,
context references, and route/abstain decisions; deterministic code validates
and applies every patch. Do not train the model to rewrite arbitrary history or
source files.

The next paired evaluation should compare, on the same seeded coding episodes:

1. Full transcript history.
2. Existing Wrench compaction/retrieval behavior.
3. Validated structured state plus latest observation and exact evidence refs.
4. The same structured-state runtime with the reviewed local LoRA updater.
5. Frontier-only execution as the quality and token baseline when separately
   authorized.

Use actual multi-step repository tasks with code edits, tests, regressions,
interruptions, external state changes, and recovery. Count all prompt,
completion, retry, validation, compaction, cache, and recovery tokens at every
model tier. Report task success and source/evidence recovery separately from
compression ratio. Preserve the historical event log outside the prompt. The
95% gate must hold over the frozen workload mix, not only at 100-step horizons.

## Primary source

- Badhe, Tiwari, and Chung, [SKILL.state: Scalable Long-Horizon Agent Skills](https://arxiv.org/html/2608.26263), arXiv v3, 2026-09-02. Table 6 reports the simulated software-repository results; Table 4 reports the public interactive benchmarks; Section 7 lists the sufficient-state and history-dependent limitations.
- The adjacent coding-specific baseline remains [SWE-Pruner](https://arxiv.org/abs/2601.16746), which reports 23–54% multi-turn coding-agent token reduction. [SWE-Pruner Pro](https://arxiv.org/abs/2607.18213) reports up to 39% prompt-plus-completion savings using a hidden-state pruning head on larger coding backbones. Neither establishes 95% on Wrench.

No model, provider, or gateway request was run for this literature review. The
host remains below its 10% RAM runtime floor; no training, inference, benchmark,
or delegation was started. The 95% token and 95/5 task-routing claims remain
unproven for Wrench.
