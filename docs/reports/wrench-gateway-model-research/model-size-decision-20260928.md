# Model-size decision for the Wrench gateway

Date: 2026-09-28 (America/Edmonton)  
Decision scope: research selection, not runtime or training admission  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256 after owner update: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

Refresh note: this report is the earlier selection snapshot. The active goal
and Iteration 142 answer-blind local results were reconsidered in the
[Iteration 143 model-size refresh](model-size-decision-refresh-iter143-20260928.md).
Use that report for the current provisional ranking; this earlier report and
its recorded goal hash remain historical evidence.

## Decision

For the Wrench Layer 1 gateway, the best current parameter-size hypothesis is
**about 2B parameters, specifically the already inventoried
`Qwen/Qwen3.5-2B`, with a Wrench-specific LoRA for bounded evidence selection
and context decisions**. It is the best fit to the job Wrench needs the model
to do: preserve task-relevant lines from noisy tool output, choose among
validated keep/retrieve/compact/stop/abstain proposals, and leave repository
facts, access, verification, and recovery to deterministic code.

This remains a model-selection recommendation, not an observed Wrench winner.
The 2B LoRA has not been trained or run here. It is not being proposed as the
standalone coding agent for an eight-hour engineering day. In the intended
hybrid, the stronger downstream model writes and repairs code; the local
controller plus deterministic Wrench runtime reduce what the downstream model
must reread. A fresh base 0.8B CUDA code task loaded successfully but generated
220 tokens of an incomplete function in 65.233 seconds; deterministic parsing
failed. Missing optimized CUDA kernels make that latency a runtime-stack
measurement, not a lower bound on optimized performance. This task joins the
previous 0.8B Wrench semantic-screen failure; the scoped 0.8B LoRA diagnostic
remains unrun. The 2B candidate is justified by multiple
independent signals below, not by assuming that the 0.8B failure generalizes.
A newer Paritok-4B result is the closest located end-to-end compression
comparator, so 4B is the first challenger after a named 2B failure. Its paired
quality evidence does not establish 95% retention, and its hardware setup does
not establish fit on this host. See the [evidence refresh](model-size-evidence-refresh-20260928.md).

If one local model must also be the coding worker, **there is no proven
all-day winner in the 0.5B-12B range**. Qwen3.5-9B and Gemma 4 12B are higher
capability research challengers. Qwen3.5-4B is a more practical intermediate
comparison on this 16 GB GPU, but its smooth local serving and repository-task
quality are also unmeasured. None has Wrench eight-hour evidence.

## Evidence by size and role

| Size/model | Evidence relevant to Wrench | Decision |
|---|---|---|
| 0.5B-0.8B, Qwen3.5-0.8B | Wrench's tool-backed semantic screen scored 0/10; vendor BFCL-V4 was 25.3 and TAU2-Bench 11.6. Iteration 106 loaded the pinned 0.8B BF16 snapshot on CUDA, but its bounded code-generation task ended at a 220-token limit and failed syntax verification after 65.233 seconds. Iterations 117/119 passed four exact synthetic lookups; Iteration 119's 3-case matrix passed 3/3 with 7/7 quotes and 88.9590% input reduction at context budget 160. Iteration 121 passed the same 3 cases at the first tested budget of 64, improving target-tokenizer input reduction to 91.3482% (19,337 to 1,673 tokens); budget 48 omitted required evidence for one case. Iterations 122/123's parser and fail-closed controls passed, and Iteration 124 passed 3/3 through Wrench's real snapshot-bound rule route plus three abstention controls. This supports deterministic handling of the known mechanical slice, not unseen repository work. None is evidence of open-ended coding, frontier savings, or LoRA value. | Keep as smallest control and compare it on bounded semantic decisions where deterministic mechanics fail closed; do not select it as the code worker. |
| **2B, Qwen3.5-2B** | A LoRA-tuned model on the closely matched Squeez task removed 92% of tool-output input tokens, with 0.86 recall and 0.80 F1 over 618 manually reviewed held-out observations. Qwen's same-family BFCL-V4/TAU2 scores are 43.6/48.8 versus 25.3/11.6 at 0.8B. The existing pinned inventory is 2,274,069,824 parameters and 4,571,274,023 bytes across 13 files; the card identifies Apache-2.0 and task-specific fine-tuning as an intended use. | **Lead controller candidate.** Lowest size with a direct task-specific LoRA result and materially better same-family tool scores. The external result measures one-observation evidence extraction, not end-to-end task success. |
| 4B, Qwen3-4B-Instruct-2507 / Paritok | Paired SWE-bench Lite compression evaluation over 300 tasks; 27.8% line-numbered context, 122/300 versus 109/300 solved, paired quality-retention CI [79.2%,100%], McNemar p=.079. Training used H100 80GB BF16; the paper's deployment target is 24GB GPU. | Closest external task-linked compression comparator and first challenger after a named 2B failure. It does not prove 95% retention or fit on this host. |
| 4B, Qwen3.5-4B | Vendor reports LiveCodeBench v6 55.8, BFCL-V4 50.3, and TAU2-Bench 79.9. Its pinned 14-file BF16 tree is 9,342,907,469 bytes. The existing Ollama Q4 package is a different artifact and its `desktop` route is currently unreachable; forced SubRoute mode would send requests to OpenRouter. | Separate base-model capacity challenger, not the Paritok model or controller lead. No model load, LoRA fit, or coding episode is admitted by this decision. |
| 9B, Qwen3.5-9B | Vendor reports LiveCodeBench v6 65.6, BFCL-V4 66.1, and TAU2-Bench 79.1. The model card lists a substantially larger checkpoint tree than 4B. | Useful ceiling for a separate local coding-worker comparison. Higher benchmarks do not prove a full workday or justify gateway overhead. |
| 12B, Gemma 4 12B Unified | Google reports LiveCodeBench v6 72.0 and Tau2 average 69.0. Gemma 4 E4B reports 52.0 and 42.2 on those metrics, respectively. These are vendor tables from a different family and evaluation setup, so compare them only in a common Wrench harness. | Research-only upper-size challenger. No pinned local inventory, Wrench adapter, hardware fit, or license/runtime admission was completed here. |

**Audit correction, Iteration 127:** the exact-answer 0.8B local-model prompts
in Iterations 117, 119, 121, and 125-127 included the expected answer in the
question text. Their model answer passes are therefore contaminated and do
not establish independent retrieval quality. Keep the token counts and
resource measurements as measurements of those exact prompts, but do not cite
their completion rates as evidence for selecting a task-quality winner. An
answer-blind paired rerun is required.

The 2B identity and file total are pinned in [Iteration 037](../../evals/wrench-gateway-model-research/iteration-037-qwen-inventory-and-subroute-liveness-20260927.md).
The Qwen benchmark figures are model-card results and are not a cross-family
head-to-head. They provide screening evidence only. The 2B LoRA evidence is
from the [Squeez paper](https://arxiv.org/html/2604.04979), whose manually
curated set contains 618 individual tool observations from 27 tool families.
It measures overlap with labeled evidence spans. The authors explicitly do
not test downstream end-to-end completion on full agent trajectories.

### Why 2B over 4B as the gateway default

The controller should specialize in an information-preserving transformation,
not absorb the coding worker's general reasoning job. The 2B evidence directly
matches that transformation and demonstrates that a LoRA can learn it. Moving
from 2B to 4B buys higher vendor coding/tool scores, but Wrench's hard problem
is end-to-end evidence and routing quality per unit of cost, not benchmark
maximum. A 4B challenger should replace 2B only if the paired Wrench
development set identifies a specific 2B capacity failure and the added
quality pays for its extra local latency, compute, and memory.

The owner now selects by measured fit on this host rather than a sub-8GB
deployment assumption. Qwen3.5-2B remains the strongest controller hypothesis
because task-matched LoRA evidence and same-family tool scores align with its
bounded role. Its local inference and training fit remain unmeasured here.
Iteration 105 rejected the installed 4B Docker CPU-only route, not the 4B model
on host CUDA. Iteration 106 shows the 0.8B host-CUDA path loads, but fails this
code task and runs slowly with missing kernels. Do not infer fit or quality
from parameter count or idle VRAM; require the frozen common task battery and
the 10% RAM/VRAM floor for each finalist.

## What token reduction has actually been demonstrated

These figures answer different questions and must not be merged:

| Evidence | Measured result | Scope and limit |
|---|---:|---|
| Synthetic E0 context demo, Iteration 098 | **86.4327%** pooled prompt-input reduction (19,289 to 2,617 tokens), with 7/7 required quotes visible | Three synthetic cases include 240 repetitive health-log lines. No real coding task, generated answer, verifier outcome, local model, frontier call, or task-success measure. See [Iteration 098 context demo](../../evals/wrench-gateway-model-research/iteration-098-context-demo-mvp-20260928.md). |
| Stable-root E0 budget sweep, Iteration 111 | **89.2270%** pooled prompt-input reduction (19,289 to 2,078 tokens), 7/7 required quotes visible; 3/3 exact repeats | Best of 897 synthetic budget settings across the same three cases. 824 settings prepared; 73 failed closed on required-evidence omission. The result is reproducible mechanics evidence, not a model or frontier-call outcome. See [Iteration 111](../../evals/wrench-gateway-model-research/iteration-111-stable-context-budget-sweep-20260928.md). |
| Required-source priority and stable-root E0 sweep, Iteration 112 | **90.6216%** pooled prompt-input reduction (19,289 to 1,809 tokens), 7/7 required quotes visible at every setting; 3/3 exact repeats | A bounded code fix made required source IDs mandatory before optional retrieval. All 897 settings prepared successfully. This is still synthetic prompt-input mechanics, not a model, task-success, or frontier-call result. See [Iteration 112](../../evals/wrench-gateway-model-research/iteration-112-required-source-priority-and-context-sweep-20260928.md). |
| Same-root paired E0 sweep, Iteration 113 | **90.6942%** pooled prompt-input reduction (19,289 to 1,795 tokens), 7/7 quotes visible; 3/3 exact repeats | Same source root and snapshot as Iteration 111. The fix recovered all 73 prior fail-closed budgets, introduced no new failures, and passed all 897 settings. This remains synthetic prompt-input evidence, not frontier-token savings or task completion. See [Iteration 113](../../evals/wrench-gateway-model-research/iteration-113-full-fixed-root-paired-sweep-20260928.md). |
| OpenCode read-tool cycle, Iteration 101 | **42.2967%** fewer target-token input tokens across two requests (13,306 to 7,678) | One scripted synthetic read round-trip; no model-produced success or provider usage. See [Iteration 101](../../evals/wrench-gateway-model-research/iteration-101-opencode-read-tool-cycle-20260928.md). |
| Current Wrench deterministic context-selection screen | **12.11%** ratio-of-sums input reduction (11.64% arithmetic mean) over five synthetic pairs | Two positive evidence-selection errors were also recorded. This is a prompt-input proxy, not frontier usage or a task-success comparison; full-lifecycle Wrench frontier savings remain N/A. See the [local direction closure](../../reports/wrench-local-acceptability/direction-closure-20260926.md) and [Iteration 025](../../evals/wrench-gateway-model-research/iteration-025-request-accounting-gap-20260927.md). |
| Squeez, 2B LoRA tool-output extraction | **92%** of the individual tool observation removed | 618 curated observations; 0.86 recall / 0.80 F1. Not 92% of complete frontier requests or episodes. |
| SKILL.state, 200-step simulated warehouse | **97.57%** fewer total tokens than its stateful baseline (122,384 vs 5,041,164), with score 0.94 vs 0.88 across five seeds | A controlled synthetic state-tracking task, not software engineering. On its simulated software-repository task, 100-step SKILL.state used 90,200 vs 923,164 tokens and scored 0.78 vs 0.53. This supports validated external state, not an identical Wrench result. |
| StateComp long-horizon benchmark | 52.27% total tokens saved overall; **38.89%** on its Code slice | A learned state-aware compressor; coding slice remains far below 95%. |

The largest external numbers are component or synthetic-runtime results. The
largest Wrench prompt-input reduction is the 90.69% same-root paired synthetic E0 context demo;
the 42.30% lowered-request cycle and 12.11% screen answer different questions.
The three-case E0 demo's repetitive synthetic logs sharply limit
generalization. There is **no eligible matched frontier-token pair**.
Consequently the current Wrench frontier-token savings result is **N/A**, not
90.69%, 90.62%, 89.23%, 86.43%, 42.30%, 12.11%, 92%, or 97.57%.

A single 92%-removal tool-output filter cannot by itself deliver a 95%
end-to-end frontier-token reduction. If fraction `p` of baseline frontier
input tokens comes from that filterable material, its idealized contribution
before overhead is `0.92 * p`. The system must also prevent some frontier
episodes entirely, remove other repeated/schema/history tokens, or both.
Because escalated tasks can be longer than local tasks, the episode escalation
rate does not substitute for measuring token-weighted savings. Every replay,
retry, verification, compaction, recovery fetch, cache miss, and frontier
response must enter the same paired ledger.

## Execution direction

1. Keep deterministic parsing, source hashing, allowlists, schema validation,
   state merge/rollback, tool authority, and exact retrieval in code.
2. Resume the in-progress E0 state-source reacquisition work. Preserve hot code,
   active diffs and test failures losslessly; retain originals and fetch by
   exact identity when evidence is needed again.
3. Measure schema filtering and context preparation at the actual OpenCode
   lowered-request boundary with the target tokenizer. Attribute these savings
   separately from local model calls and from the LoRA's contribution.
4. After package review and safe resources, compare 0.8B control, 2B LoRA, and
   a deterministic-only arm on identical synthetic development cases first.
   Train only from approved train rows, use dev for tuning, and keep held-out
   data sealed. Advance to 4B or larger only for a named, measured capacity
   error.
5. On a separate, rights-cleared frozen coding workload, compare the full
   hybrid against frontier-only with verified task outcomes, target-tokenizer
   and provider receipts, complete retries/recovery, latency, compute, and
   labor. Do not open paid traffic until the route's numeric aggregate spend
   cap is set and enforced.
6. Continue toward the 95/5/95 and 95%-cheaper confidence-bound gates. Then run
   the already specified paired eight-hour sessions across unrelated repos,
   languages, tests, interruptions, restarts, and regressions. No synthetic
   screen or model-card result substitutes for those gates.

## Current admission state

- `127.0.0.1:4000` read-only GETs returned HTTP 200 for liveness, model
  catalog, and active-model status. Active mode is `openrouter`, forced, policy
  4. No completion, provider call, credential read, or route change occurred.
- Iteration 106 completed one local 0.8B CUDA code-generation smoke and failed
  deterministic syntax verification; it was not a Wrench-context or LoRA
  evaluation. At report time, free RAM recovered to 21.48% and GPU memory to
  15,216 MiB. Fit-03 still needs >=25% RAM at start and an independent exact
  package review against the active goal hash.
- Before authoring this report, the storage checker included the Docker model
  volume, both Wrench automation directories, sibling/worker repositories,
  and legacy Wrench temporary roots. It reported 22,400,487,149 actual bytes
  and 7,603,000 active reserved bytes against the 50,000,000,000-byte ceiling.
  This documentation job reserved 1,000,000 bytes. C: had 143,675,453,440
  bytes free at admission.

## Primary sources

- [Pinned Qwen3.5-2B model card and benchmark table](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/README.md)
- [Pinned Qwen3.5-2B file inventory](https://huggingface.co/api/models/Qwen/Qwen3.5-2B?blobs=true&revision=15852e8c16360a2fea060d615a32b45270f8a8fc)
- [Squeez: task-conditioned tool-output pruning](https://arxiv.org/html/2604.04979)
- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Pinned Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B/blob/cc5442c03a5c0bff0bd4c6888d9a40029c637733/README.md)
- [Gemma 4 model card and benchmark table](https://ai.google.dev/gemma/docs/core/model_card_4)
- [Gemma 4 deployment and memory guidance](https://ai.google.dev/gemma/docs/core)
- [SKILL.state: Scalable Long-Horizon Agent Skills](https://arxiv.org/html/2608.26263)
- [StateComp: Learning When to Compress History in Long Horizon Agents](https://arxiv.org/abs/2609.27298)
- [Wrench state-aware compression evidence, Iteration 093](../../evals/wrench-gateway-model-research/iteration-093-statecomp-coding-context-evidence-20260928.md)
