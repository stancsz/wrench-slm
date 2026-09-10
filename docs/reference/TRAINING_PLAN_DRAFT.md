# Wrench-SLM next training phases

Status: Draft for discussion, 2026-09-09. This document proposes work; it does not authorize a training run, service change, dataset promotion, or deployment.

## Purpose and success condition

Wrench is a local specialist for predicting the next routine developer tool call from the context available before a cloud model generates it. Its output is a precise tool call or an explicit fallback. The gateway owns execution permissions, execution, and the envelope sent to the cloud model.

- For eligible read operations, the gateway can execute the prediction and supply the real result with the cloud request.
- For operations that change state, Wrench supplies a draft for review through the existing authorization flow.
- For ambiguous, unsupported, or reasoning-heavy requests, Wrench yields to the cloud model.

Flash targets a roughly 135M CPU/Pi deployment; Pro targets a roughly 0.5B workstation/GPU deployment. Product success means correct, useful predictions that eliminate otherwise necessary tool-generation turns and reduce total latency and token use while preserving task quality. The cloud may still reason, verify drafts, and produce the final response.

Training loss, valid JSON, teacher agreement, and command exit status are supporting measurements. None independently establishes this success condition.

## Proposed sequence

Prove the training and measurement machinery, rebuild the data, establish a Pro SFT baseline, validate constrained decoding and selective use, test GRPO, develop Flash, then measure the complete speculative workflow.

### Phase 0: Freeze the task contract and repair training correctness

Define exactly what Wrench sees: the relevant user request, bounded recent conversation and tool results, supported tool signatures, operating system and shell, working directory, and required runtime identifiers. Capture only information available at the prediction point. The future teacher call and its result must never enter the model input.

Define one tool-call schema and one fallback representation across datasets, SFT, grammar, rewards, evaluation, and the gateway. Keep execution eligibility in the gateway; a generated confidence or safety label must not grant permission.

Repair or retire the audited paths:

- Deterministic token IDs, a serialized tokenizer, and checkpoint compatibility checks. Existing native checkpoints need their original vocabulary mapping established before reuse.
- Correct SFT batching, completion-only labels, and identical prompt construction during training and inference.
- Length handling that preserves complete targets. Bucket long examples or explicitly exclude them from the supported scope, recording exclusions. Never silently train on a cut-off answer.
- Exact argument comparisons, explicit evaluation failures, and metrics tied to an actual checkpoint.
- Separate candidate training from serving. Preserve optimizer, scheduler, RNG, tokenizer, code revision, and dataset version for resumable runs.
- Regression tests for the review findings, including reward direction and sample alignment before any GRPO experiment.

**Exit:** A small training run has finite gradients, learns a tiny diagnostic dataset, reloads in a fresh process with identical tokenization and deterministic predictions, and resumes successfully. The tiny-set result is a machinery check only.

### Phase 1: Build a dataset for actual speculative prediction

Preserve existing root splits and the candidate build as source artifacts. Produce a separately versioned dataset and manifest.

Reconstruct real request/context-to-next-call examples where logs permit. Keep command-copying examples as a separately measured capability. Traces without recoverable prior context can support formatting exercises, but cannot establish intent understanding. Keep observed calls, verified executions, and teacher-generated examples distinguishable.

Start with bounded Git inspection, file reading/search, environment inspection, and diagnostics. Then add state-dependent stdin and lifecycle calls, plus bounded edit drafts with sufficient context. Include Windows and POSIX cases, English and Chinese, unseen paths, quoting, whitespace, missing arguments, and unsupported or ambiguous requests. Confirm execution eligibility per operation and environment rather than assuming every invocation of a command such as pytest or curl is read-only.

Split by original conversation/session and seed family before generating variants or upsampling. Put all derivatives in the same split. Create train, development, calibration, and sealed final-test partitions, including unseen repository and later-time slices where available. The current contaminated held-out set becomes legacy development evidence.

Use the configured MiniMax teacher for candidate generation and the configured frontier teacher for difficult cases and disagreement review, recording the resolved model. Validate labels against schemas, environment prerequisites, and task-specific expected outcomes. Teacher approval alone does not make an execution label correct. Freeze a data-generation budget before acquisition.

**Exit:** No exact cross-split examples or shared source families; no future information in inputs; every retained target is complete; provenance, exclusions, family counts, tool coverage, and length distributions are reported. Data volume follows verified coverage rather than a row-count quota.

### Phase 2: Establish a Wrench-Pro SFT baseline

**Recommended review decision:** Start with the pretrained Qwen2.5-0.5B-Instruct route already named in the project specification, using its original tokenizer and architecture. This is a pretrained Wrench-Pro derivative. It is not equivalent to training the custom Wrench05BConfig from scratch.

Pin the base revision and environment. Start with the specification's LoRA rank 16, alpha 32, and dropout 0.05. Profile batch size and sequence lengths on the 16 GB GPU before choosing a full-run configuration. Record the learning-rate schedule and training budget; select checkpoints using development metrics with an early-stopping rule.

Compare the unchanged base, deterministic baseline, and SFT model on identical inputs. Score unconstrained outputs separately from grammar-constrained outputs. Report each tool, language, OS, argument-complexity, and input-length slice. Keep early capabilities in replay as harder examples are introduced.

**Proposed development exit:** At least 99.5% valid tool outputs and 95% task success on the declared supported routine slice, with per-slice results and uncertainty reported. Correct abstention is scored separately. These are development thresholds, not production authorization. The SFT model must demonstrate improvement on natural-language requests and unseen entities, not only explicit command-copying inputs.

### Phase 3: Validate constrained decoding and selective use

Integrate the actual tool schemas with the selected tokenizer. Exercise incomplete JSON, escaping, Unicode, EOS, generation limits, and fallback. The boundary must return a validated complete call or an explicit fallback, including timeout and invalid-generation cases. Report these fallbacks so a schema metric cannot hide failed generation.

Calibrate the decision to offer a call on the calibration partition. Measure correctness versus coverage. Average token probability is a candidate signal to test, not an assumed probability that the whole action is correct. Test unseen paths, paraphrases, changed numeric arguments, missing state, and multi-intent requests.

**Exit:** Select an operating point with declared coverage and error bounds, no protocol failures escaping the boundary, and no observed unauthorized pre-execution in the test suite. The project's 70% routine coverage remains a goal to measure, not a reason to lower correctness requirements. Measure successful eligible reads, accepted write drafts, and fallback separately.

### Phase 4: Run a bounded GRPO experiment

Begin only after the SFT and decoding gates pass. Implement completion-token policy gradients with the correct sign, aligned rewards, and multiple outputs per identical prompt. Preserve optimizer state and document the policy-ratio, clipping, and reference-policy settings.

Use training-only tasks with executable checks: correct argument binding, expected file content or state transition, and appropriate fallback. Syntax or exit code zero alone cannot earn a correctness reward. Run generated operations only in controlled environments appropriate to the task. Include both useful local completions and necessary fallbacks so neither indiscriminate execution nor universal abstention wins.

Compare SFT plus grammar against GRPO plus the same grammar, with matched evaluation conditions. Predeclare the run budget and selection rule. Evaluate reward exploitation using development cases; do not compute training rewards on the sealed test set.

**Exit:** Keep GRPO only if it improves task success or useful coverage at the same error limit without worsening important slices. If it does not, retain SFT and record the negative result. GRPO is an experiment, not a requirement to ship a useful specialist.

### Phase 5: Develop Wrench-Flash and verify hardware feasibility

Use the same contract and independently partitioned evaluation suite. Compare a pretrained 135M student trained on verified examples against one additionally trained on verified Pro/teacher outputs. A model card candidate is SmolLM2-135M-Instruct; selection remains open pending language coverage, runtime, and latency checks. Do not transfer Pro's scores to Flash or assume it needs the same breadth.

Measure Flash before and after quantization. Validate export correctness and complete-call behavior on the actual intended Pi/CPU hardware. Profile Pro inference on the workstation as well. Measure tokenization, prefill, time to first token, full-call generation, grammar overhead, memory, and concurrency separately. Begin feasibility measurements during Phase 2 to expose problems early.

**Exit:** A separately evaluated Flash checkpoint has an explicit supported scope, acceptable quantization regression, and actual hardware measurements. Current documents disagree about latency and memory thresholds; reconcile them before setting the final pass criteria. Keep full-call latency distinct from first-token latency and external tool runtime.

### Phase 6: Validate end-to-end value and controlled updates

Run a shadow evaluation first. Compare baseline gateway behavior with Wrench-assisted behavior on matched tasks and environment snapshots. Include prediction overhead, speculative work, teacher verification, rejected drafts, retries, total cloud input/output tokens, and final task quality. Use resettable fixtures for execution comparisons; state-changing drafts remain subject to the existing review path.

Only after a checkpoint is selected, open the sealed test for final release evaluation. Any subsequent tuning informed by it requires a fresh independent final test. A later live canary needs an explicit rollout decision, a fixed checkpoint, and a rollback target.

Replace automatic training on the serving model with a versioned process: collect traces, curate labels, add replay, train a candidate, evaluate, and promote only after acceptance. Monitor new tool signatures, unsupported inputs, drift, and end-to-end outcomes.

**Exit:** Measured net latency/token improvement at maintained task quality, supported by complete receipts, plus a demonstrated rollback. A higher local-call count alone is not acceptance.

## Decisions for our review

1. **Model origin:** Follow the pretrained Pro/LoRA route, or make training an original foundation model a separate primary objective? Recommendation: pretrained Pro first. A from-scratch route needs its own tokenizer, corpus, compute budget, and scaling study.
2. **First capability scope:** Recommendation: bounded read/inspection calls first, then contextual interaction tools and edit drafts. Each still uses the same full tool-call contract.
3. **Deployment order:** Recommendation: establish Pro as a correctness reference, then develop Flash with early CPU feasibility measurements.
4. **Acceptance contract:** Reconcile conflicting latency definitions, memory ceilings, and confidence thresholds before release selection. Declare supported scope and measure useful coverage, correctness, and total workflow cost together.

## Sources

- Current project purpose: [goal.md](../../goal.md).
- Existing SFT, grammar, and GRPO direction: [SPECIFICATION.md](SPECIFICATION.md).
- Existing deployment goals: [PRODUCTION_ACCEPTANCE_STANDARD.md](PRODUCTION_ACCEPTANCE_STANDARD.md) and [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md).
- Training review in this conversation, 2026-09-09. Its reproductions concern the current code and datasets, not a complete new model evaluation.
- [Qwen2.5-0.5B-Instruct official model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct).
- [SmolLM2-135M-Instruct official model card](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct).
