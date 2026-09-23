# Model and benchmark lineage

This note pins the model identity behind the current external Wrench gate
results. It keeps the transferred structural-prune model separate from later
profile-guided candidates.

## Model used by the completed BFCL, ToolBeHonest, and When2Call gate runs

- Upstream checkpoint: [`Qwen/Qwen3.6-35B-A3B`](https://huggingface.co/Qwen/Qwen3.6-35B-A3B).
- Run receipt model directory: `D:\models\Wrench-Qwen3.6-8expert-BF16`.
- The [Phase 24 prune receipt](../../phases/phase-24-structural-prune-baseline/prune-receipt.json)
  identifies this as an explicit expert selection retaining source expert IDs
  0 through 7 from 256 experts. It records `weights_modified: false` and
  `EXPERIMENTAL_UNCALIBRATED`.
- The transferred artifact is pinned by commit
  `e0ebd6f3762e30a118ade6bc47e01fc65d8e3eea` in the private artifact repo,
  as recorded in
  [`MODEL_ARTIFACT_TRANSFER.md`](../../docs/archive/2026-09-22/MODEL_ARTIFACT_TRANSFER.md).
- The transfer receipt reports 3,945,236,336 state-dict elements including
  visual tensors and 3,881,244,016 text-only runtime parameters. The nine BF16
  shards occupy about 7.9 GB on disk. These numbers describe different things.
- The paired binary decision head has SHA-256
  `e33e28af544be5eaf156ff42dbe47d2098a36939bb4b0cfd0222d378d4ee3b0b`, 4,098
  parameters, and a frozen threshold of 0.5. Its receipt says the Qwen base
  weights were not updated, no provider was called, and the final evaluation
  split was not read.

The completed BFCL, ToolBeHonest, and When2Call runs used this model directory
and head hash. Those scores are binary gate decisions only. The adapters did
not generate proposals or execute tools, so they cannot establish final-agent
success or verifier safety.

The selected ARB V2 retrieval score uses `ContextLedger.search`, not the binary
head or the Qwen checkpoint. Its completed, pre-BM25 full ranking run scored
all 427 cases: Recall@20 0.2338, MRR 0.0812, and canonical BCY@8K 0.0669,
below the reproduced official Lexical baseline. The search implementation has
since changed to BM25 term-frequency normalization. That candidate has not
been scored yet, so the completed pre-change numbers remain the only Wrench
ranked-retrieval result and must not be attributed to the new code. This is a
retrieval-component result, not a model or end-to-end agent score.

A separate ARB-adapted binary abstention run used this checkpoint and head,
with local Qwen3.5 0.8B and 9B comparisons on the same 427 cases. It is not an
official ARB retrieval score. Wrench scored 55.27% binary accuracy versus
61.36% for Qwen3.5 9B, whose paired repository-cluster interval favors 9B.
The input-limit and no-gold caveats are recorded in the ARB runbook. The
separate CodeScale, ContextBench, and SWE-Explore scorecards evaluate other
components and must retain their own model, adapter, and run identities. See
[`external/agent-retrieval-bench/RUNBOOK.md`](external/agent-retrieval-bench/RUNBOOK.md).

## Separate profile-guided candidate

[Phase 25](../../phases/phase-25-router-profiling/README.md) records another
8-expert selection based on measured Qwen routing activity, plus 16- and
32-expert tiers. Its compact text-only tier has the same reported parameter
count but a different per-layer expert-selection rule and a different
artifact identity. It is not the model used by the three completed gate runs
above. Do not merge scores from the two candidates.

The profile-guided run receipt documents a 20-request teacher profile and a
selection rule based on per-layer expert activation counts. Those structural
and runtime smokes do not establish benchmark quality or production value.

## Identity fields for future comparisons

Every scorecard should record:

1. Upstream model ID, exact artifact commit, and artifact file hashes.
2. Expert-selection recipe, parameter count basis, quantization, and runtime.
3. Binary head hash, prompt/feature adapter, threshold, and verifier version.
4. Dataset revision and case IDs, benchmark source revision, parser, and
   metric implementation.
5. For outside models, exact model revision, serving/runtime setup, and the
   same prompts, cases, output parser, and scorer wherever a direct comparison
   is claimed.

The outside scores in the phase README are benchmark-published references.
Unless both runs share the same cases and protocol, they are context for the
comparison, not a Wrench-versus-model result.
