# Product proof design and independent audit

Date: 2026-09-27
Status: protocol design only; no product-task or paid comparison was run
Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)

## Independent audit

Two read-only assignments reviewed candidate fit and the current success/cost
evaluation design. Both verified HEAD `af01304824f079a64b6c3902397a2034b843511a`
and their assigned source hashes before and after inspection. They changed no
files, did not open held-out contents, and did not download, train, infer, call
a provider, or spend.

| Assignment | Nonce | Reviewed repository files at the time of audit |
| --- | --- | --- |
| `WRENCH-MODEL-FIT-AUDIT-20260927-01` | `4c76fe77-15ae-4550-a62d-90fe8ff0fa92` | Goal `17AB8BE22658105B79C9C7425F3F26579FAECC84BC7FC2CA4B6A3BF372025292`; research report `BCE0BEF398C505AF823C6241E4BD0A83F9DEF400E97D2C1F3AD95F434D03A925`; fit protocol `7F894E578C2264190DFF551499C0C83194F49431DC383E9825DC458630589557`; iteration log `75FE87325506A9CDE0E8C6A04401556F0D95D5E3A9BD8068F7B12957C568D1B7`; trainer `D1EA068B5EFEACD7A318EBFF4217FACFD1FA01AF3B7FB8CE08689AD18728B5CE`; pinned-tree tool `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `WRENCH-EVAL-PROOF-AUDIT-20260927-01` | `07c694b0-2c2c-46c0-8d71-86172f31ce36` | Goal `17AB8BE22658105B79C9C7425F3F26579FAECC84BC7FC2CA4B6A3BF372025292`; research report `BCE0BEF398C505AF823C6241E4BD0A83F9DEF400E97D2C1F3AD95F434D03A925`; held-out protocol `2D6CA677A1A000C1820302B6501E390813CE6CC4574BF28EE694BA060F5BD53B`; fit protocol `7F894E578C2264190DFF551499C0C83194F49431DC383E9825DC458630589557`; iteration log `75FE87325506A9CDE0E8C6A04401556F0D95D5E3A9BD8068F7B12957C568D1B7` |

These hashes identify the reviewed pre-integration state. This report and the
goal have since been updated with the findings below; a new exact-hash review
is required before using changed goal/protocol identities to admit training.

The current synthetic split contains 128 cases per split: 104 LOCAL (81.25%),
8 FRONTIER (6.25%), and 16 ABSTAIN (12.5%). Even perfect classification cannot
show at least 95% local completion and no more than 5% frontier use on this
distribution. The held-out protocol is limited to deterministic schema/policy
mechanics and has no frontier-only arm or provider calls. It cannot prove task
success retention, frontier-token savings, or all-in cost savings.

The previous goal table also omitted paired success retention against a
frontier-only baseline and the original 95%-cheaper requirement. This protocol
adds those measures. Any claim must keep all planned episodes in the
denominator, including failure, abstention, timeout, and human rescue, so
unsuccessful tasks cannot disappear from the reported rate.

## Paired task experiment

Use a preregistered, rights-cleared and consented task collection. Freeze each
repository snapshot, task statement, tool set, time budget, evaluator, and
starting context. Pair every episode across three arms:

1. **Frontier-only:** the pinned strong model completes the task directly.
2. **Deterministic Wrench + frontier:** the deterministic context runtime
   handles retrieval and verification; the same frontier model performs
   delegated engineering.
3. **LoRA Wrench + frontier:** the same runtime and frontier model, with the
   candidate LoRA making only its reviewed bounded controller proposals.

The frontier route and model revision, tool/runtime versions, task order,
retry policy, cache policy, and output limits are frozen before scoring.
Independent evaluators score repository tests and task-specific acceptance
criteria without seeing the treatment arm. Do not tune on the sealed final
split. Keep training, development, and final sets separated by repository,
task family, and time where feasible.

Each episode receives one exhaustive terminal disposition: local verified
success with no frontier call, frontier use, local failure/no answer,
abstention, or human rescue. Also report whether frontier-only succeeded and
whether each hybrid arm achieved a verified pass. A human rescue does not
convert a model failure into a pass.

## Primary acceptance metrics

The five primary claims below apply to the LoRA Wrench hybrid arm. Each bound
is one-sided 99% (`alpha=0.01`) under the preregistered Bonferroni plan,
controlling family-wise error at 0.05 across those five claims. The
deterministic Wrench + frontier arm is a separate secondary control; it does
not borrow this primary error budget. If confirmatory claims are later required
for that arm, preregister the expanded multiplicity plan before enrollment.
Use inference aligned to the frozen repository/workday cluster structure and
task-family strata/weights.

| Claim | Estimand | Required bound |
| --- | --- | --- |
| Local agents do at least 95% of work | Episodes with verified completion and no frontier call divided by every planned episode | Lower bound >= 0.95 |
| At most 5% frontier use | Episodes with any frontier call divided by every planned episode | Upper bound <= 0.05 |
| Preserve at least 95% of frontier-only work | Verified LoRA-hybrid passes on tasks that frontier-only passes divided by frontier-only verified passes; report the deterministic hybrid as a separate secondary result | Lower bound >= 0.95 for the LoRA hybrid |
| Save at least 95% of frontier tokens | `1 - hybrid_frontier_tokens / frontier_only_frontier_tokens`, using paired sums for the same tasks | Lower bound >= 0.95 |
| Cost at least 95% less all-in | `1 - hybrid_all_in_cost / frontier_only_all_in_cost`, including frontier charges, measured local compute/energy, and preregistered training/evaluation amortization | Lower bound >= 0.95 |

The route and token gates have different denominators. For paired planned
episodes `i`, let `b_i` be frontier-only provider tokens and `h_i` be all
hybrid frontier tokens for that episode. The token gate requires
`sum(h_i) <= 0.05 * sum(b_i)` independently of the episode gate
`count(frontier-routed episodes) / count(all planned episodes) <= 0.05`.
Routing 5% of episodes does not imply 95% token savings: the routed set may
contain a larger share of baseline token volume. If the routed 5% account for
12% of baseline tokens, a full-context request for each uses 12% of baseline
tokens and saves only 88%; to pass, all remote work on that set must consume at
most 41.7% of its baseline frontier-token volume, before any additional calls.
Report the baseline token mass represented by routed episodes and all paired
token totals. Do not average per-episode savings percentages or infer token
savings from route counts.

Count every frontier input and output token, cached input, retry, verifier,
fallback, compaction, re-fetch, and auxiliary model call from auditable
provider receipts. Report raw episode counts, denominators, confidence bounds,
latency, local tokens, GPU/CPU time, energy assumptions, all-in dollars, and
failures for all arms. A 95% reduction in frontier tokens does not imply 95%
lower all-in cost.

For an unadjusted single-endpoint Bernoulli illustration (`alpha=0.05`), 234
independent episodes with at most 6 adverse outcomes give an exact one-sided
95% upper bound of 4.99784%. This is not the Bonferroni-adjusted primary bound
for the five-gate experiment.
At a true 2% adverse-event rate, that rule has 80.91% probability of passing.
This is only a planning floor under independence. Repo/task/time clustering,
paired success and continuous token/cost ratios, and simultaneous claims need
their own power analysis and usually a larger sample. With zero observed
events, 59 independent episodes only barely put the one-sided 95% upper bound
below 5%; that design has about a 30% chance of seeing zero events when the
true rate is 2%. Do not use a case-level bootstrap over four synthetic task
families as population evidence.

### Ratio estimands, weighting, and cluster-inference lock

This amendment makes the five primary estimands and their confidence gates
explicit. Let `w_i` be the task's frozen target-population weight. Use `w_i=1`
only for a self-weighting task sample. Let `L_i` be a verified local hybrid
pass with no frontier call, `E_i` indicate any frontier event in the hybrid
arm, `H_i` be hybrid verified pass, and `F_i` be frontier-only verified pass.
For the hybrid frontier token total use `h_i`; for the frontier-only arm use
`f_i`; use `a_i` and `b_i` for the corresponding all-in costs.

| Primary estimand | Frozen estimator | One-sided gate |
| --- | --- | --- |
| Local completion | `sum(w_i L_i) / sum(w_i)` | Lower bound `>= 0.95` |
| Frontier episode share | `sum(w_i E_i) / sum(w_i)` | Upper bound `<= 0.05` |
| Frontier-success retention | `sum(w_i H_i F_i) / sum(w_i F_i)` | Lower bound `>= 0.95` |
| Frontier-token ratio | `sum(w_i h_i) / sum(w_i f_i)` | Upper bound `<= 0.05` |
| All-in cost ratio | `sum(w_i a_i) / sum(w_i b_i)` | Upper bound `<= 0.05` |

Compute token and cost estimands as ratios of weighted totals, never as the
average of episode-level ratios or savings percentages. Do not drop failed,
abstained, timed-out, or rescued episodes. Missing usage or price receipts make
the affected token or cost estimand unmeasured. A zero frontier-only
denominator, including a resample with no frontier-only passes for the
retention endpoint, is not a pass. Preserve it as an unestimable replicate and
classify the campaign as inconclusive unless the preregistered interval method
handles it conservatively.

Preserve each paired task and every treatment arm together in every resample.
The resampling unit must follow the frozen sampling design, not the individual
row count. Freeze population weights, repository IDs, task-family strata,
workday/session IDs, cluster intersections, and any multiway dependence before
enrollment. Task-family labels are required coverage strata with preregistered
weights; four fixed labels are not four independent population clusters. If
repositories and workdays are crossed, use a justified multiway cluster
procedure; if the actual design is nested, use the corresponding highest-level
independent cluster. Do not select a bootstrap method after observing results.

The existing minimum of three repositories and ten workdays is a coverage and
repeatability floor, not proof of adequate cluster degrees of freedom. Few-
cluster methods can have serious size errors, and multiway dependence requires
an inference method that matches the crossed structure. The final sampling
frame must simulate the complete paired analysis before enrollment: vary
cluster counts and imbalance, within-cluster dependence, task-family weights,
pass correlation, and token/cost tail behavior; check coverage at each null
boundary and joint power at the preregistered plausible alternative. Require
at least 80% joint power across all five gates, or label the result a
pilot/inconclusive. Do not adopt the IID 234- or 398-episode floors as the
product sample size. See the [few-cluster inference review](https://onlinelibrary.wiley.com/doi/10.1111/ectj.12107)
and [multiway clustering method](https://www.nber.org/papers/t0327).

## Full-day engineering check

Run a separate preregistered eight-hour workday study across at least three
unrelated repositories and two languages. Include real edit/test/review loops,
context compaction and exact-source re-fetch, task switching, interruptions,
process/session restarts, and recovery after failed edits. Predeclare quality,
completion-time, regression, correction, human-rescue, timeout, and recovery
thresholds. Report all tasks and operator interventions. Synthetic routing
cases, long transcripts, or code benchmark scores cannot satisfy this
criterion.

Task data must have a documented rights and consent basis. The current
synthetic-only training authority does not authorize collecting private user
work or training on public benchmarks. Paid 4000-route calls require the
owner's numeric spend cap, a pinned upstream provider/model identity, and an
auditable per-request usage receipt method before dispatch.

## Candidate-fit audit

The audit recommends keeping the model role explicit:

- **Qwen3.5-0.8B:** existing gateway-controller baseline. It is small and
  already staged, but no adapter or quality result exists, and fit-02 remains
  behind the 25% RAM start gate.
- **Qwen3.5-2B:** best next gateway-controller capacity challenger if the
  0.8B candidate demonstrates a measured capacity failure. Its pinned tree
  is 4.56 GB and a separate cache plus working snapshot is about 9.12 GB.
  Adapter-target compatibility and a short LoRA preflight remain unverified.
- **Qwen2.5-Coder-1.5B-Instruct:** a code-specialized challenger if the model
  itself must rank code evidence or propose bounded code edits. Its pinned
  tree is 3.10 GB and its official card describes a conventional 1.54B causal
  decoder with 28 layers and 32,768-token context. That is architecturally
  simpler than the Qwen3.5 hybrid path, but a separate runner and exact PEFT
  target-module review are still required; it has no Wrench fit or all-day
  coding result.
- **Qwen3.5-4B:** plausible later inference ceiling at a short context, with a
  pinned 9.34 GB tree. FP32 base weights alone are about 16 GB before training
  activations, so the current trainer cannot be reused. A quantized training
  path would need new architecture review and preflight.
- **Gemma 4 E2B-it:** separate function-calling comparison, 2.3B effective /
  5.1B total parameters and a 10.28 GB pinned tree. Google's inference
  estimates do not establish QLoRA fit; duplicated cache and working copies
  would use about 20.56 GB before training outputs and logs.

The recent host snapshot was an RTX 5060 Ti with 16,311 MiB VRAM, about
15.1 GiB free, 17.74% free system RAM (5.66 GiB), and 145.75 GiB free on C:.
This is adequate idle VRAM for smaller-model experiments, not proof of
training memory or smooth all-day operation. Do not start the existing fit-02
until it meets its 25% RAM start gate. Each alternative model needs its own
pinned inventory, storage reservation, target-module review, exact-hash
review, and monitored preflight above the 10% RAM and VRAM floors.

Sources: [Qwen2.5-Coder-1.5B official card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct),
[pinned Qwen3.5-0.8B tree](https://huggingface.co/Qwen/Qwen3.5-0.8B/tree/2fc06364715b967f1860aea9cf38778875588b17),
[pinned Qwen3.5-2B tree](https://huggingface.co/Qwen/Qwen3.5-2B/tree/15852e8c16360a2fea060d615a32b45270f8a8fc),
[pinned Qwen3.5-4B tree](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a),
[Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4),
and [Gemma 4 memory estimates](https://ai.google.dev/gemma/docs/core).

Additional primary sources: [Qwen3.5 Transformers implementation](https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_5/modular_qwen3_5.py), [SWE-Pruner](https://arxiv.org/abs/2601.16746), [LLMLingua-2](https://arxiv.org/abs/2403.12968), [PA-Tool (ACL 2026)](https://aclanthology.org/2026.acl-long.948/), and [Qwen3.5 hybrid LoRA placement study](https://arxiv.org/abs/2604.22127) (single seed; non-Wrench tasks).

### Model-role and context-pruning research refresh

The current official Qwen3.5-2B card describes a 2B multimodal model with a
hybrid layout of Gated DeltaNet and full attention, 24 layers, and a native
262,144-token context. Its vendor-reported general-agent results include
BFCL-V4 43.6 and TAU2-Bench 48.8, compared with 25.3 and 11.6 for Qwen3.5-0.8B.
These are useful reasons to test it as a **bounded controller capacity
challenger**, not evidence it can deliver full-day engineering or meets
Wrench's thresholds. The current Transformers source defines projections
that match the runner's target-suffix allowlist, but no exact 2B checkpoint
load, PEFT attachment, target count, peak-memory, or inference-path check has
been run. Review those candidate-specific properties before any
download/training admission. The [official Qwen3.5-2B card and benchmark
tables](https://huggingface.co/Qwen/Qwen3.5-2B), which also warns of thinking
loops in the 2B model, and the [pinned official
config](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/config.json)
support these architecture claims.

Qwen2.5-Coder-1.5B is a distinct code-specialist lane: its [official
card](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct) specifies a 1.54B
causal language model, RoPE/SwiGLU/RMSNorm, 28 layers, and 32,768 context. The
card describes code-generation/fixing training but does not establish coding
agent success. Current Wrench training code is pinned to Qwen3.5 and has
Qwen3.5-specific projection suffixes; this coder model needs a new target map,
candidate-specific source/protocol review, and bounded preflight. It is a
candidate for source ranking or small patch proposals, not a substitute for a
strong model on multi-file diagnosis.

For compaction, [LLMLingua-2](https://arxiv.org/abs/2403.12968) formulates
compression as token classification with a bidirectional encoder and reports
3x-6x compression-model speedups and 1.6x-2.9x end-to-end latency speedups at
2x-5x compression on its evaluated benchmarks. That supports evaluating
extractive token selection as a separate option against free-form summaries;
it does not establish fidelity for source code or Wrench repositories. Wrench
must preserve exact source references and hot code, and test that compressed
context preserves task pass rates. Use a Wrench-specific LoRA for bounded
policy/evidence/abstention behavior; compare model-specific tool/schema naming
as a separate ablation rather than expecting the adapter to repair interface
misalignment. The [ACL 2026 PA-Tool study](https://aclanthology.org/2026.acl-long.948/)
reports up to 17% tool-selection gains and 80% fewer schema-name hallucinations
from a training-free schema-alignment method on its benchmarks. This is
motivation for schema controls, not a replacement for the requested LoRA.

The coding-specific [SWE-Pruner preprint](https://arxiv.org/abs/2601.16746)
reports 23%-54% token reduction from a task-aware 0.6B line selector on
multi-turn agent tasks such as SWE-Bench Verified. Its up-to-14.84x compression
is on single-turn LongCodeQA. These paper results do not show a 95% reduction
for iterative coding sessions, and code-context pruning must still be checked
against task success and exact-source recovery.

LoRA placement is also an experimental variable. A 2026 preprint directly
studying Qwen3.5-0.8B compared attention-only, recurrent/Gated DeltaNet,
MLP-only, and full-layer adaptation. On its instruction/math tasks,
softmax-attention-only used 24 modules / 1.08M trainable parameters versus
186 modules / 10.82M for all layers and often matched or exceeded the broader
adapter. It also reported severe degradation when adapting the recurrent path
for some task domains, and HumanEval pass@1 remained <=0.6% across tested
sub-1B placements. The paper is a single-seed study on non-Wrench tasks, so it
is not a Wrench result. Still, the current Wrench runner targets all 186
projection modules. Before a full fit, add an attention-only LoRA candidate
as a resource-efficient controller ablation beside the existing all-module
candidate, with matched synthetic train/dev rows and untouched heldout. Do not
assume attention-only is best for code generation. See [Where Should LoRA Go?](https://arxiv.org/abs/2604.22127).

The most credible sequence is therefore: keep the existing 0.8B synthetic
controller as the smallest baseline when the 25% RAM start gate passes; use
exact deterministic retrieval and source-linked, reversible compaction for
mechanical work; review Qwen3.5-2B module/runtime fit if a measured controller
capacity failure appears; and separately compare Qwen2.5-Coder-1.5B only if
code reasoning is an explicit local duty. Neither the 0.8B nor 2B model should
be described as able to code productively all day until the paired workday
protocol passes. End-to-end issue fixing requires multi-file context,
execution, and verification, as reflected in the [ICLR SWE-bench task
definition](https://proceedings.iclr.cc/paper_files/paper/2024/hash/edac78c3e300629acfe6cbe9ca88fb84-Abstract-Conference.html).

## Preregistration lock amendments (third-review closure)

The third read-only proof-spec critique (`WRENCH-PROOF-SPEC-CRITIQUE-20260927-01`,
nonce `b361d558-0e70-4206-8ad5-556b8e35d20a`) confirmed that the earlier
revision was directionally sound but still not preregistration-ready. It
verified HEAD `af01304824f079a64b6c3902397a2034b843511a` and the six assigned
document hashes before/after review, made no changes, did not inspect held-out
payloads, and used no model, network, provider, or spend. This section resolves
its findings and supersedes any less-specific or conflicting wording above.

**Treatment and success claim.** Every 95/5/95 and 95%-cheaper threshold is a
separate gate for the LoRA Wrench + frontier arm. Report deterministic Wrench
+ frontier as a separate control. Never pool the two hybrid arms. For each
episode, log task pass/fail, frontier-only pass/fail, route events, abstention,
timeout/failure reason, and human intervention as orthogonal fields. A
frontier call can coexist with any terminal outcome; it is not itself a
terminal outcome. Keep all planned episodes in denominators. A human rescue is
not a model pass.

**Population and splits.** Before enrollment, define the target population,
repository types, languages, task families/difficulty, source window, intended
workload weights, sampling probabilities, and inclusion/exclusion rules. Use
mandatory repository-, task-family-, and time-isolated final data. The current
LoRA authority is synthetic-only: evaluation work must not be used to train or
tune the adapter. If rights/consent or group/time separation cannot be
established, restrict the conclusion to a labeled pilot for that corpus and do
not claim general engineering effectiveness. Report the population to which
the measured rate applies.

**Paired execution.** Run each arm in an isolated workspace cloned from the
same frozen repository and working-tree snapshot. Randomize or counterbalance
arm order. Predeclare cache/session reset behavior, identical tool versions,
permissions, budgets, stop rules, and evaluators. Evaluators must be blind to
the arm. No task may inherit another arm's edits or state.

**Escalation and accounting.** Only an external frontier/provider call counts
as a frontier escalation. Local compaction, local retrieval, and local retries
do not count toward the 5% rate, but their tokens, latency, compute, energy,
and effect on outcome remain in the local/all-in record. Any remote verifier,
retry, fallback, re-fetch, or compaction does count. For frontier token totals,
sum provider-reported prompt plus completion tokens; a cached-input field is a
subset of prompt tokens and must not be counted twice. Keep raw receipt fields.
Calculate billed dollars from a pinned price snapshot, separately applying
cache pricing, discounts, and fees. Missing or inconsistent receipts make the
affected claim unmeasured.

All-in cost uses the same declared categories across arms: frontier charges,
local inference and measured energy, hardware/runtime allocation, LoRA
training and evaluation amortized over a preregistered horizon and expected
episode volume, retries, and operator time including human rescue at a
preregistered loaded rate. Publish the price schedule, energy method,
hardware allocation, amortization horizon/volume, and labor rate before
unsealing results. Report components as well as the total.

**Power and multiplicity.** Use one-sided confidence bounds for every primary
claim and control family-wise alpha at 5% with a declared method such as
Bonferroni. Before enrollment, publish the endpoint-specific power simulation,
analysis code, minimum independent repository/task-family/workday clusters,
and stopping rule. The 234-episode calculation above is only a single-endpoint
IID illustration. The actual sample must account for clustering, both arms,
paired pass retention, token/cost ratios, and multiplicity. Until the workload
frame and cluster counts are frozen, no final sample size is admitted. If the
available sample cannot meet the powered design, report a pilot, not a pass.

**Operational full-day gate.** Use 10 independent paired eight-hour sessions,
at least three unrelated repositories and two languages, at least five task
episodes per session (50 minimum total), and at least two edit/test loops per
session. Across sessions include issue repair, feature work, test repair,
refactor/maintenance, and review corrections. Each session includes a context
switch, interruption, and process/session restart. Apply the primary bounds to
this workload and report each day separately. At least 9/10 LoRA sessions must
complete eight hours with no product/runtime stall longer than ten minutes;
all episodes remain accounted for; all injected recovery cases must restore
the correct snapshot and provenance; 95th-percentile recovery is at most ten
minutes; and there must be zero severity-1/2 regressions, lost work, or
unauthorized actions under a severity rubric frozen before enrollment. Human
rescues remain failures under the same 5% bound.
These ten sessions are a repeatability gate, not a substitute for powered
population-level evidence.

## Current disposition

The active hourly heartbeat is configured. Fit-02 has not started; no model
was downloaded; no held-out content or paid route was accessed. This file
defines future evidence requirements and does not itself establish any target.
\n