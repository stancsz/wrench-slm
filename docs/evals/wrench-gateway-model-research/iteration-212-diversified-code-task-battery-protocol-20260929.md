# Iteration 212 protocol: diversify the local code-task battery

Date: 2026-09-29 (America/Edmonton)  
Protocol job: `WRENCH-CODETASK-MVP-ITER212-PROTOCOL-20260929-01`  
Nonce: `f626720e-fd45-41cb-917c-dce1600ae726`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`  
Heartbeat-declared goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (still differs from the file on disk)

## Gap and scope

Iteration 211 completed one paired code repair with both arms passing, but one synthetic episode cannot establish representative coding success, model-size choice, or all-day engineering. This protocol advances the named gap by specifying a diversified pilot before another model run. It does not amend the gateway's completion, routing, success-retention, Frontier-token, all-in-cost, or sustained-engineering targets.

The next pilot will contain 12 newly authored, synthetic-only episodes across three independent fixture repositories. Each repository will have four task forms: (1) code localization with exact source evidence, (2) a small function repair with behavior tests, (3) test/log diagnosis with a constrained evidence-linked result, and (4) a configuration or documentation change whose exact required facts can be checked deterministically. At least two task forms must require a code artifact. Tasks and verifier oracles must be frozen before inference. The current `retry-function` fixture remains a historical smoke and is excluded from this pilot's success denominator.

This is a feasibility pilot, not a confirmatory acceptance sample. The 12 episodes must span more than one source snapshot and task family, and each episode is one paired comparison. No result from this pilot may be described as a population success rate or as proof of the 95% target. For reference, with zero failures, at least 59 independent successes are needed for a one-sided 95% exact binomial lower bound to reach 95%; clustering by repository/task family and paired success-retention uncertainty require additional design and may require a larger sample.

## Frozen comparison

For each episode, use the same pinned local model, task wording, decode settings, verifier, fixture snapshot, and evidence requirements in both arms:

1. **Full-context baseline:** task plus the complete frozen synthetic repository context.
2. **Wrench-prepared:** the same task plus deterministic Wrench context preparation, exact source references, required hot evidence, and auditable omissions/recovery handles.

The first candidate for the pilot is the already inventoried Qwen3.5-4B BF16 base, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. This is only a continuation of the local demo, not a declaration that 4B is the overall best size. No LoRA is loaded in this arm. Compare Wrench deterministic preparation separately from any future 2B controller or LoRA arm; the current product acceptance still requires the trained bounded LoRA hybrid.

Balance which prompt arm runs first across episodes using a frozen seed. Do not tune prompts, retrieval weights, compression budgets, acceptance oracles, or code against the pilot holdout after observing model outputs. If pilot findings change the harness, create a new versioned battery and preserve all prior receipts unchanged.

## Deterministic verification and containment

- Parse code candidates with a language-specific, explicit allowlist before executing any candidate. Run only fixed tests in an isolated synthetic fixture; generated code cannot access arbitrary shell, network, credentials, or the real repository.
- Check exact evidence IDs/quotes for localization and diagnosis tasks. Check behavior and configured edge cases for code changes. Check exact keys/values and required references for configuration/documentation tasks.
- A task is complete only when every predeclared correctness and evidence check passes. A verifier crash, missing source, stale handle, incomplete response, timeout, and human rescue remain failures or explicit abstentions in the denominator.
- The Wrench arm may perform only predeclared bounded retries and recovery fetches. Record every attempt and fetched source. Never hide a failed first attempt behind a passing retry.
- No provider or SubRoute requests. Any later fixed response demonstration must be marked `mock` and excluded from provider-use and cost evidence.

## Required receipt and metrics

Freeze one manifest before the run with task IDs, fixture/repository group, snapshot and source hashes, task/verifier hashes, prompts, tokenizer/model identity, output limits, retry/recovery policy, local route, primary metrics, and stopping rules. Write a no-clobber receipt containing every planned episode, both arms, all output hashes, exact model/runtime identity, token counts, verification outcomes, failures/abstentions, retry and recovery traces, input and output latency, peak/series RAM and VRAM, and resource-monitor errors.

Report two separate local tokenizer measures:

- Input prompt reduction from actual token IDs passed to generation, with context-preparation target counts kept as a separate diagnostic.
- Full-lifecycle local-token reduction using all generated attempts' actual input plus output IDs. Do not call either quantity Frontier savings.

Also include context-build and verification wall time, cache state/misses, CPU/GPU use where available, resource reserve minima, human/operator intervention, and energy if it can be measured with a pinned instrument. If energy or all-in cost cannot be measured, report `null`; do not impute a zero. Reconcile tokenizer target counts against actual generation IDs, retaining both values and any difference.

## Admission and stopping gates

Before the eventual run, create a new execution job ID and nonce; re-read the current goal and source hashes; check storage status and reserve a bounded peak under 50 GB including existing reservations and external roots; verify at least 5 GiB C: headroom; and confirm no duplicate output or live job. Keep at least 10% system RAM and VRAM free for the whole run. Sample in-process and independently cross-check GPU telemetry before and after generation. Stop and mark the entire affected pair incomplete on a resource-floor breach, telemetry failure, model/source/goal identity mismatch, output conflict, or snapshot drift. A completed pair cannot override those integrity failures.

This protocol does not authorize a download, inference run, training job, activation, provider call, or opening the sealed final LoRA split. A separate future execution admission must have its own reservation and exact bounded output plan. Any training package review must use the actual current gateway-goal hash; the mismatch recorded above must be reconciled before hash-bound training review.

## Decision use

Use the pilot to decide whether the local demo is stable enough to expand to a prepowered, repository-grouped coding evaluation. If the contexts omit required evidence, if the model cannot produce verifier-passing changes, or if local latency/resource costs erase practical value, preserve that failure and revise the deterministic runtime or candidate before the confirmatory set. Do not select a model size from this pilot alone.
