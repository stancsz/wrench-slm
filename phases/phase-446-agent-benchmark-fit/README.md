# Wrench benchmark slate and evidence

Updated 2026-09-23.

## Decision

The slate is **five scorecards: one internal product scorecard and four
external benchmarks**. The external choices are the strongest task fit for
what Wrench is built to do: retrieve repository evidence, provide useful
context within a fixed budget, and improve a coding agent without taking over
its write authority. We chose Agent Retrieval Bench V2, CodeScaleBench,
ContextBench, and SWE-Explore-Bench because each has a public task set,
reproducible metrics, and published outside-model or outside-system results.
The slate is fit-first, not a promise that Wrench will win every scorecard.
Direct Wrench-versus-model claims require matched tasks, interface, budget,
and evaluator.

**Showcase order:** lead with the internal paired workflow scorecard as the
product proof, then Agent Retrieval Bench V2 as the clearest external
component-level result. Use CodeScaleBench next when its matched run can show
whether Wrench changes the same outside agent's task reward, cost, or latency.
ContextBench and SWE-Explore-Bench are independent quality checks on context
and exploration; their current weak results belong in the report as gaps, not
as Wrench wins. This order highlights measured strengths without hiding the
hard comparisons.

**What currently looks strongest:** on 427 Agent Retrieval Bench V2 rows, the
BM25 retrieval candidate raised Wrench's canonical BCY@8K from 0.067 to 0.119
with a paired 95% interval of +0.007 to +0.098. Recall@20 and MRR gains remain
inconclusive, and the result is below published Qwen embedding references. It
is a real component-level improvement, not proof of end-to-end utility.

**The internal gate story is safer decisions, with useful coverage still the
gap:** on V7's fresh, scope-correct 80-case development split, Wrench scored
58/80 (72.5%), accepted 10/32 supported requests, and made zero unsafe
continuations. Qwen3.5 9B scored 67/80 (83.75%), accepted 27/32, and made 8
unsafe continuations among 48 boundary cases. The paired accuracy interval
includes zero; Qwen's balanced-accuracy lead is statistically clear on this
small split. In the secondary plain-prompt condition, Wrench scored 64/80 with
zero unsafe continuations while Qwen scored 34/80 with 46 unsafe
continuations. Keep the original system-prompt comparison primary. V6's
scope-corrected result and the Qwen3.5 27B comparison remain separate prior
receipts. No head is enabled. Report the safety/coverage tradeoff and every
selected result, including negative or incomplete results.

The internal scorecard also includes a bounded-gate head-to-head against
Qwen3.5 9B and 27B on identical development cases, while its main result
remains the complete matched workflow.

The owner-approved objective is to use this slate to improve Wrench in the
bounded categories it is designed for. Qwen3.5 9B is the primary outside-model
target; Qwen3.5 27B is the stretch target. The first predeclared categories
are safe binary tool eligibility and retrieval quality, measured with paired
case-level comparisons on frozen data. For binary gating, Wrench must retain
zero prohibited accepts while improving correct eligible acceptance and
overall outcomes. The latest head does not yet meet this gate. For retrieval,
the BM25 candidate produced a paired budgeted-context-yield gain over the
previous Wrench component, but remains below published outside-model
references. Compare against outside models only when the same task IDs, input,
ranked-result budget, and evaluator are available. The 44-case gate result and
the new 80-case candidate comparison remain separate development receipts.
Latency is a separate metric, not a substitute for accuracy. This improvement
target remains open until new held-out evidence verifies it.
The step-by-step, split-safe candidate protocol is in
[`MODEL_IMPROVEMENT_PLAN.md`](MODEL_IMPROVEMENT_PLAN.md).

On the frozen 44-case development comparison, Wrench at its calibration-set
threshold scored 40/44 (90.9%) with zero unsafe continuations. Qwen3.5 9B
scored 35/44 (79.5%) with 9 unsafe continuations. The paired template-cluster
95% interval for Wrench's accuracy advantage is 0.0 to 23.3 percentage points,
so the point estimate is favorable but not conclusive. Wrench p50/p95 decision
latency was 175/202 ms versus 268/309 ms for Qwen3.5 9B. Qwen3.5 27B scored
44/44 with zero unsafe continuations, at 4,927/5,289 ms p50/p95. These are
development gate results, not full workflow outcomes or release evidence.
All four Wrench false negatives are eligible `git_read_status` prompts (0/4
accepted at the calibrated threshold); the other five action families have no
eligible misses in this 44-case slice. The next gate-model milestone is to
recover these simple read-only status requests while retaining zero unsafe
continuations, then confirm on a separate unsealed evaluation before making a
model-quality claim.

| # | Scorecard | Why it showcases Wrench | Public metrics | Outside-model reference | State |
| --- | --- | --- | --- | --- | --- |
| 1 | **Wrench paired workflow utility** | The product proof: whether a bounded Wrench worker improves task success, safety, speed, and frontier-token use against stronger-model-only and rules-plus-fallback workflows. | Final task success and safety, eligible correct acceptance, prohibited accepts, end-to-end p50/p95 latency, net frontier-token savings, plus gate accuracy and paired 95% confidence intervals. | Matched stronger-model-only teacher arm; local Qwen3.5 9B and 27B gate comparisons. | Latest V7 gate development comparison: Wrench 58/80 (72.5%), 10/32 eligible accepted, zero unsafe continuations. Qwen3.5 9B: 67/80 (83.75%), 27/32 eligible accepted, 8/48 unsafe continuations. The paired accuracy interval includes zero; the balanced-accuracy gap favors Qwen. Plain-prompt results favor Wrench (64/80 vs 34/80) but are secondary. V6 and Qwen3.5 27B receipts are prior candidate comparisons. Full three-arm workflow replay remains required. |
| 2 | [**Agent Retrieval Bench (ARB) V2**](https://github.com/eyuansu62/agent-retrieval-bench) | **Best current positive component story:** Wrench's retrieval candidate increased useful files in a fixed context budget, and the benchmark also includes natural no-gold cases for selective behavior. | Recall@20, MRR, canonical budgeted context yield (BCY@4K/8K/16K/32K), selective success and coverage. | Public Qwen3-Embedding-4B/8B, Jina code embeddings, RepoMap, lexical, and BM25 references; same-row outside-model reruns are the direct-comparison path. | On 427 identical rows, the BM25 candidate improved Wrench BCY@8K from 0.067 to 0.119, with paired repository-bootstrap 95% CI [+0.007, +0.098]. Recall@20 and MRR gains are inconclusive, and Wrench remains below the published Qwen embedding references. A component gain, not end-to-end proof. |
| 3 | [**CodeScaleBench**](https://github.com/sourcegraph/CodeScaleBench) | **Outcome-level tool value:** its paired design isolates whether adding repository intelligence changes an outside coding agent's results. | Paired task-reward delta, retrieval Precision/Recall/F1@10, wall time, and cost. | Published Claude Code + Haiku 4.5 baseline with and without Sourcegraph MCP. A direct Wrench comparison must use the same agent and model on the paired tasks. | Frozen roster contains 370 matched reward tasks. Wrench adapter and matched run pending; the published MCP result is a design reference, not a Wrench result. |
| 4 | [**ContextBench**](https://contextbench.github.io/) | **Context quality with a path to agent outcomes:** measures line-level retrieval now; a matched solver can later connect retrieval quality to task Pass@1. | Line precision, recall, Context F1; Pass@1 and cost only with a matched downstream coding agent. | Published openJiuwen + DeepSeek-V4-Pro, GPT-5, Claude Sonnet 4.5, Qwen3-8B, and Qwen2.5-32B. Same-case local Qwen reruns are required for direct model comparison. | Pinned 500-row verified subset. The corrected full pre-BM25 run is active with 302 detail rows saved. The earlier 184-row interruption came from a dataset alias that hid three distinct FasterXML module repositories; the adapter now maps each instance to its canonical module repo. The separate 3-case engineering slice was weak (line recall 0.0287, precision 0.0162, derived F1 0.0207), so do not present that pilot as a full-suite score. |
| 5 | [**SWE-Explore-Bench**](https://github.com/Qiushao-E/SWE-Explore-Bench) | **Repository exploration quality:** scores whether Wrench can find the right files and line regions before a solver edits anything. | Line precision/recall/F1, hit-file and hit-region rate, noise, context efficiency, rank-aware quality at fixed region budget. | Published GPT-5.4-family, Claude Code, Codex, OpenHands, Mini-SWE-Agent, and specialist localizers. Direct comparison requires the same ranked-region interface and cases. | Official 848-row data and issue/base-commit mapping are pinned. Pilot F1 was 0.0243 against saved outside-trajectory references of 0.4722–0.8361. The full pre-BM25 run remains active: 296 detail rows are flushed, with 317 scorer completions observed on the latest poll. This is a baseline, not a Wrench win. |

## Why these four external benchmarks

The four were chosen before candidate results because their tasks stay close
to Wrench's read-only authority and make its contribution measurable. ARB V2
is the best direct retrieval fit and the strongest current positive result.
CodeScaleBench tests whether repository intelligence changes the outside
agent's final task reward, speed, or cost. SWE-Explore measures ranked file
and line localization. ContextBench measures what a coding agent explored and
used, with task success as a downstream outcome when the same solver is run.
These provide complementary evidence from component retrieval to workflow
impact, while keeping the limits of each layer visible. Each has public
metrics and outside-model/system references. Only matched reruns support a
direct model claim.

BFCL V4 and NVIDIA When2Call were checked and kept as diagnostics instead of
showcase entries. BFCL's 240 selected irrelevance cases all require no-call
behavior and contain no Wrench-allowlisted function; an always-abstain baseline
scores 100%, versus 61.7% for the prior Wrench head. When2Call's 3,652 prompts
contain no eligible Wrench tool calls, and 65.2% exceed Wrench's input limit.
Their official results are useful outside references, but these adapted
projections do not fairly measure Wrench's supported actions. The detailed
receipts remain in `benchmark-manifest.json` and `external/`.

The external scorecards measure complementary layers. CodeScaleBench grades
the paired impact of adding Wrench, ContextBench grades context use during
coding, SWE-Explore grades ranked file/line evidence, and ARB stresses
next-file retrieval and selective abstention. The internal scorecard includes
both the gate-level Qwen comparison and the complete matched workflow. Do not
average the five scorecards into one score. Only the internal matched-workflow
result can establish Wrench's release value.

The active ContextBench and SWE-Explore runs loaded the pre-BM25 ContextLedger
implementation. ContextBench has 300/500 saved rows after correcting its
dataset-alias-to-module-repository map; the earlier 184-row stop was an
adapter mapping problem, not a benchmark-data failure. SWE-Explore has 272
flushed rows and a latest observed scorer count of 312/848. Neither measures
the later BM25 candidate. On ARB V2,
the BM25 candidate's canonical BCY@8K is 0.1193 against the pre-change 0.0669,
with paired repository-cluster 95% CI for the gain [0.0071, 0.0978]. Recall@20
and MRR improved by 0.0307 and 0.0044, but both intervals include zero. All
candidate outputs and paired intervals are in
`external/agent-retrieval-bench/runs/wrench-context-ledger-bm25-v1/`.
The loaded baseline is pinned in the manifest by Git blob
`0dc7e14e6e1e3f656c7b340e18c5c620d2e89476` and SHA-256
`4aa54990a2908c8ee94ae4373eb52074d32880bbafbdfa83d661084b9e87e6d8`. The
updated runners now record component identity at startup so future runs cannot
mistake a later working-tree hash for the code held in memory.

### External benchmark showcase order

Lead with the **internal paired workflow scorecard** for product value, then
**ARB V2** as the strongest completed external component result. Its paired
component change improved BCY@8K over the previous Wrench retrieval path, but
remains below published outside embedding references. **CodeScaleBench** is
the next external priority because its paired design tests whether adding
Wrench changes the same outside agent's task outcomes, speed, or cost; it
stays pending until that matched run is complete. Use **ContextBench** and
**SWE-Explore-Bench** as independent context and exploration checks, including
their current weak results. This reports one measured component improvement,
one pending product-impact test, and two diagnostic scorecards without
counting overlapping metrics as four separate proofs of value.

This is a fit-based slate, not a promise that Wrench already wins these tests.
The current SWE-Explore and ContextBench evidence is weak, so those results
must be presented as gaps until improved by legitimate product work and rerun
on frozen data. ARB now has a paired budgeted-context-yield improvement over
the prior Wrench retrieval path, while remaining behind outside embedding
references. The current V7 Wrench-vs-Qwen3.5 9B gate comparison shows zero
unsafe continuations and much lower eligible coverage for Wrench; it does not
show an accuracy win. Do
not substitute a broad benchmark with an unrelated tool set to manufacture a
better-looking number.

## Showcase selection rule

Select benchmarks because their task and evaluator match Wrench's authority:
read-only retrieval, useful context, and measurable tool contribution. Keep
patch-generation, arbitrary-shell, broad REST, and transactional tasks outside
the showcase because they score capabilities Wrench is not designed or
authorized to perform. Do not select or drop a benchmark after seeing its
Wrench score. Publish each selected result with its exact split, outside model,
adapter, budget, and evaluator identity. Published leaderboard rows are
comparison context only; call a result a direct outside-model comparison only
when Wrench and that model use the same tasks, prompts, harness, parser, budget,
and scoring path.

### Why these four external benchmarks

- **SWE-Explore-Bench** isolates repository exploration and scores the file
  and line evidence before patch generation.
- **ARB V2** measures workflow-derived file retrieval and preserves natural
  no-gold cases for separate selective-retrieval and abstention results. The
  ranking result counts only after Wrench returns real ranked candidates.
- **ContextBench** adds human-annotated context quality and downstream
  success, efficiency, and cost under a fixed coding-agent setup.
- **CodeScaleBench** provides the clearest outside tool-impact design: the same
  agent and model run on matched tasks with and without retrieval tooling.
  Wrench remains read-only; the benchmark agent retains its own permissions
  inside disposable task sandboxes.

### Outside models and comparison rules

Every published leaderboard value below is an outside reference, not a
Wrench-versus-model result. A direct comparison requires the same task IDs,
outside solver/model, prompt, context budget, harness, parser, and scoring
path. Keep local-model reruns separate from published leaderboard results.

| Benchmark | Published outside references | Direct comparison rule |
| --- | --- | --- |
| CodeScaleBench | Claude Code + Haiku 4.5: pinned snapshot reports mean reward 0.5357 vs 0.5647 over 371 results per arm; technical report reports +0.0349 paired reward delta over 370 matches and $0.7333 vs $0.5121 cost over 392 pairs. | Keep artifact populations separate. For a direct Wrench result, hold outside agent/model, prompt, task IDs, sandbox, and verifier constant. These are outside references, not Wrench scores. |
| SWE-Explore-Bench | GPT-5.4-family and agentic explorers including Mini-SWE-Agent, Claude Code, OpenHands, and Codex; specialist localizers include CoSIL and LocAgent. | Use the official ranked-region metrics and fixed budget. Run an outside explorer through the same adapter for a direct model comparison. |
| Agent Retrieval Bench V2 | Reproduced Lexical: Recall@20 0.4940, MRR 0.1574, BCY@8K 0.2650; Qwen3-Embedding-4B: 0.6306, 0.2379, 0.3409; Qwen3-Embedding-8B: 0.7029, 0.2336, 0.3732; RepoMap: 0.6333, 0.2158, 0.3788. | Wrench ContextLedger is scored on the same released candidates with official ranking and BCY scorers. Its current score trails Lexical; Qwen embedding leaderboard values remain published references, not paired reruns. |
| ContextBench | openJiuwen + DeepSeek-V4-Pro: recall 0.753, Pass@1 60.4%, Context F1 0.257, efficiency 0.642, cost $0.57; mini SWE-agent + GPT-5: recall 0.606, Pass@1 47.2%, Context F1 0.312. | Compare Wrench vs no-Wrench under the same fixed downstream solver and token/cost accounting. Leaderboard systems are references until task IDs and harness match. |

Do not train or tune on public test splits or the sealed Wrench final split.
Record model decisions, verifier outcomes, valid proposals, correct accepts,
abstentions, and final task success separately. Preserve the six-action
allowlist and review-only patch boundary. Do not call a paid provider for a
benchmark run without explicit authorization.

### Excluded from the showcase slate

Aider Polyglot remains a future challenge, not a showcase scorecard. Its
primary outcome depends on patch generation and test execution, which is a
poor match for Wrench's review-only proposal boundary. The separate 44-case
development proposal diagnostic emitted invalid JSON on all 44 outputs.
BFCL irrelevance, ToolBeHonest, When2Call, and RepoBench-R remain supplemental
diagnostics for the reasons recorded below; none is presented as a Wrench
strength claim.

Terminal-Bench and InterCode assume arbitrary shell use, which Wrench is not
authorized to perform. ToolBench's broad REST API catalog, tau-bench's
transactional domains, and MCP-Atlas's multi-server workflows exceed the
bounded action set. SLM-Bench measures general model quality and environmental
impact rather than the active Wrench release gates. These suites may suit
other agents, but they would misstate Wrench's role. See the
[AgentAbstain benchmark](https://agentabstain.github.io/),
[SLM-Bench paper](https://aclanthology.org/2025.findings-emnlp.1165.pdf),
[Salesforce xLAM](https://github.com/SalesforceAIResearch/xLAM), and
[Hugging Face smolagents](https://huggingface.co/docs/smolagents).

### Supplemental local outside-model diagnostic

`run_ollama_toolbehonest_baseline.py` runs public Qwen3.5 models through the
frozen ToolBeHonest case adapter. ToolBeHonest is retained as a prior
diagnostic, not as one of the selected four external scorecards. It uses the
same 700 case IDs, input text, and gold labels as Wrench, adds a JSON-only
response instruction, checks IDs and labels, and reports a paired source-record cluster-bootstrap
95% interval for the accuracy difference. It calls only the local Ollama
service, records the model digest, and has no paid provider or tool-execution
path. This is an adapted solvability comparison, not an official ToolBeHonest
leaderboard score or evidence that Wrench should accept these outside-allowlist
tools. The same runner also scored Qwen3.5 9B Q4_K_M. Both were run with
Ollama's documented `think: false` setting so the JSON response is scored, not
the separate reasoning channel. The initial 0.8B attempt without that setting
produced empty visible responses on all 700 rows; it is preserved as an invalid
protocol run and excluded from results.

A Qwen3.5 27B Q4_K_M paired baseline on these same 700 diagnostic cases
completed locally. It remains supplemental because the benchmark's tool menus
are outside Wrench's action allowlist. Keep its result separate from the
selected five scorecards and do not use it as evidence of operational tool
success.

## Current evidence

### Selected external scorecards

- **CodeScaleBench:** the frozen csb-v1-mixed371 JSON has 372 rows: 251 active, 120 backup,
  and 1 missing. Baseline and MCP each have 371 result rows, with 370 matched
  rows. The README in that pinned commit says 275, a documented lineage
  conflict. The pinned snapshot reports mean reward 0.5357 vs 0.5647 across
  371 results per arm. The separate technical report reports a +0.0349 paired
  reward delta over 370 rows and mean cost $0.7333 vs $0.5121 over 392 cost
  pairs. Keep these artifact populations separate. The source tag resolves to
  cac154c9384a78702092aaad76d29b1ac50d2982. Wrench has not been adapted or
  scored; published Sourcegraph results are outside references, not Wrench
  results. See [`external/codescalebench/RUNBOOK.md`](external/codescalebench/RUNBOOK.md).
- **SWE-Explore-Bench:** 848 issues across 203 repositories and 10 languages.
  Its exact issue text and base commits are now pinned for all 848 rows from
  four public source datasets. The source join resolves 64 unique repository
  names and 847 commits, which conflicts with the upstream README's 203-repo
  claim and is recorded as a lineage discrepancy. An 18-case stratified pilot used exact commit
  snapshots and the upstream evaluator. Wrench ContextLedger line F1 was
  0.0243, hit-file rate 0.225, nDCG@500 0.0756, and context efficiency
  0.0649. Saved trajectory references included GPT-5.4 at 0.5688 F1 and
  Gemini 3 Pro at 0.8361 F1. Wrench is behind on this repository-exploration
  component; the pilot is not a full-suite result. See
  [`external/swe-explore-bench/RUNBOOK.md`](external/swe-explore-bench/RUNBOOK.md).
- **Agent Retrieval Bench V2:** 427 samples across 25 repositories: 345
  positive workflow examples, 50 natural no-gold examples, and 32
  counterfactual controls. The official Lexical reference was reproduced on
  all 345 positives with `all_files`: Recall@20 0.4940, MRR 0.1574, and
  canonical BCY@8K 0.2650. Wrench's real `ContextLedger.search` path was then
  adapted to emit ranked files and scored on all 427 rows. On positives it
  reached Recall@20 0.2338, MRR 0.0812, and BCY@8K 0.0669. Paired
  repository-cluster bootstrap intervals for Wrench minus Lexical were
  [-0.309, -0.188] for Recall@20, [-0.111, -0.035] for MRR, and
  [-0.303, -0.079] for BCY@8K. Published same-release Qwen3-Embedding-4B
  scored 0.6306/0.2379/0.3409 and Qwen3-Embedding-8B scored
  0.7029/0.2336/0.3732 for those metrics. Those embedding results are
  published references, not case-paired reruns. These Wrench metrics are the
  frozen pre-change baseline at source blob
  `0dc7e14e6e1e3f656c7b340e18c5c620d2e89476`. The current
  `ContextLedger.search` source uses a BM25 candidate that has not yet been
  scored; see [`retrieval-iteration.md`](retrieval-iteration.md). Do not
  present the baseline as the candidate's current score.

  The separate Wrench binary gate scored 55.27% accuracy and 57.91% balanced
  accuracy; cap-matched Qwen3.5 9B scored 61.36% and 70.51%. Wrench's combined
  abstention rate over natural and counterfactual no-gold rows was 62.20%.
  Its 82% natural-no-gold abstention result in the earlier report was
  conditional on the 50-row natural subset and mostly forced by input limits.
  The ranking and binary-gate scores are distinct components, not end-to-end
  task success. ARB now provides a concrete gap signal rather than a Wrench
  showcase win. Details, hashes, and reproduction commands are in
  [`external/agent-retrieval-bench/RUNBOOK.md`](external/agent-retrieval-bench/RUNBOOK.md).
- **ContextBench:** 1,136 tasks across 66 repositories and 8 languages. The
  public leaderboard currently lists 15 agent/model systems; its top row is
  openJiuwen + DeepSeek-V4-Pro at 0.753 recall and 60.4% Pass@1. Wrench has
  not been adapted or scored. Use the fixed harness with a matched downstream
  solver.

### Aider Polyglot exclusion

Aider is pinned locally at 225 tasks across C++, Go, Java, JavaScript, Python,
and Rust, but it is excluded from the five scorecards because its primary
outcome depends on successful patch generation. The current development
proposal diagnostic emitted invalid JSON 44/44 times. Keep that as a known
proposal-path blocker, not an Aider score or a Wrench strength claim.
### Prior external probes, retained outside the selected five

- **BFCL V4 irrelevance:** the Wrench gate abstained correctly on 148/240
  non-live irrelevance rows (61.7% accuracy); 92/240 continued (38.3%
  false-continue rate). Every offered function was outside Wrench's six-action
  allowlist. An always-abstain control scores 100%. This is a weak, mismatched
  boundary probe, not general function-call accuracy.
- **ToolBeHonest Level 1:** the adapted binary projection scored 53.6%
  accuracy; continuation was 16.0% on solvable rows and 8.9% on unsolvable
  rows. The paired exact rate was 11.7%. The allowlist audit found 87/700
  unsupported-menu continuations (12.4%). These are frozen gate decisions,
  not post-verifier execution results.
- **Direct local comparison on ToolBeHonest:** Wrench scored 53.6% adapted
  binary accuracy, with 16.0% continuation on benchmark-solvable rows and 8.9%
  false continuation on benchmark-unsolvable rows. Qwen3.5 0.8B Q8_0 scored
  57.3%, continued on 98.0% of solvable rows, and falsely continued on 83.4%
  of unsolvable rows. Qwen3.5 9B Q4_K_M scored 61.6%, with 96.6% solvable
  continuation and 73.4% false continuation. Paired source-record bootstrap
  intervals for outside-model minus Wrench accuracy were +3.7 percentage
  points [1.0, 6.6] for 0.8B and +8.0 points [4.7, 11.3] for 9B.

  Qwen3.5 27B Q4_K_M completed a separate paired 700-case run on 2026-09-23.
  It scored 74.1% adapted binary accuracy versus Wrench's 53.6%; the paired
  source-record-clustered difference was +20.6 percentage points for Qwen
  (95% CI +17.1 to +24.0). Qwen's solvable-task continuation rate was 95.1%,
  and its false continuation rate on benchmark-unsolvable cases was 46.9%.
  Qwen p50/p95 latency was 5,575/6,018 ms. This is a clear result on the
  adapted solvability label, but it is not a fair operational target: all 700
  menus are outside Wrench's six-action allowlist. Keep it as a supplemental
  gap diagnostic and do not claim Wrench should continue on these cases.

  These public menus contain no Wrench-allowlisted tools. The accuracy label
  asks generic solvability, while Wrench's actual action policy should
  abstain on all 700 cases. This is a conservatism diagnostic, not end-to-end
  task success or verified safety. Both outside models are Qwen-family
  checkpoints. Warm p50/p95 decision latency was 204/274 ms for Wrench,
  140/183 ms for 0.8B, and 285/313 ms for 9B. Outside models generate JSON;
  Wrench uses a classification head, so these are component diagnostics.
- **RepoBench-R:** the pinned release contains 48,000 test rows; two rows with
  invalid gold indices are excluded by both methods, leaving 47,998. The
  current bounded client calls `ContextLedger.assemble`, not `.search`, so
  this is not an integrated-path score. Jaccard leads every easy metric and
  every @3/@5 hard metric. ContextLedger is 0.4 percentage points ahead only
  on Java hard acc@1. Treat this as a gap and keep the complete score table,
  input hashes, and invalid row IDs in the ignored local receipt at
  `external/repobench-r/runs/wrench-context-ledger-v1/summary.json`.

### Internal diagnostics

The internal scorecard is the three-arm matched workflow replay specified by
[`GOAL.md`](../../GOAL.md) and
[`WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md`](../../docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md).
It is the only scorecard that can establish release value.

Current development diagnostics are not product scores:

- On the authored 44-case development split, the frozen binary head matched
  40/44 labels, accepted 20/24 eligible cases, and abstained on all 20 labeled
  abstention cases. Warm decision latency p50/p95 was about 175/202 ms.
- A separate proposal-generation pass on those cases produced invalid JSON
  for 44/44 outputs. The verifier abstained on all 44, with zero prohibited
  accepts. That failure cannot be blended with the binary-head score.
- The 3-arm workflow replay, paired success/safety comparison, and net
  frontier-token savings remain unmeasured here.
The bounded-gate subscore compares Wrench directly with Qwen3.5 9B and 27B on
identical unsealed development cases. On the current 44-case development set,
Wrench matched 40/44 labels (90.9%) with 0/20 unsafe continuations. Qwen3.5 9B
with the original system prompt matched 35/44 (79.5%) and continued on 9/20
labeled-abstain cases (45%). Qwen3.5 27B matched 44/44 (100%), had 24/24
eligible coverage, and had zero unsafe continuations. Wrench's 9B point
estimates are better but inconclusive because the paired template-clustered
95% intervals include zero. Against 27B, Wrench was 29.5 points more accurate
with higher coverage on the plain-prompt variant, and much faster in the
capped local run. On the deployment-relevant original prompt, Qwen27B accuracy
and coverage were higher. The 27B p50/p95 was
4,927/5,289 ms, versus Wrench at 175/202 ms. These small development results
are not leaderboard scores or product proof. No sealed-split scoring is part
of this comparison.

See [`internal/README.md`](internal/README.md) for the receipts and strict
rescores.

## Supplemental diagnostic: When2Call

Keep this run for failure analysis only. The pinned test input has 3,652 rows:
1,295 `tool_call`, 1,062 `request_for_info`, and 1,295 `cannot_answer` gold
labels. It also contains `direct` distractor choices. The largest serialized
prompt plus tool menu is 23,414 characters, menus reach 37 tools, and 2,381
rows (65.2%) exceed the Wrench gate's 8,192-character limit. The binary
projection's false-continue rate on the 258 no-tool cases was 20.9%. All 1,295
gold tool-call targets are outside Wrench's allowlist, so there are no eligible
calls. Do not compare its adapted binary macro-F1 (44.3%) with the official
three-way Macro-F1.

## Model and artifact identity

Wrench's current compact model is derived from Qwen3.6-35B-A3B. The transferred
8-expert BF16 artifact reports 3,881,244,016 text-only runtime parameters
(3,945,236,336 state-dict elements including visual tensors); its approximately
7.9 GB file size is not its parameter count or runtime memory requirement.
See [`MODEL_AND_BENCHMARK_LINEAGE.md`](MODEL_AND_BENCHMARK_LINEAGE.md) for the
artifact lineage and per-run identity boundaries. Keep exact model, tokenizer,
head, quantization, and harness hashes with every new comparison.

## Reproduction and artifacts

- `benchmark-manifest.json` is the machine-readable five-scorecard decision.
- SWE-Explore-Bench, ContextBench, and CodeScaleBench adapters and Wrench runs
  remain pending. ARB Lexical reproduction and the Wrench ContextLedger ranked
  retrieval component are scored; the Wrench result is substantially below
  Lexical and is recorded as a stress-test gap. The separate binary-gate result
  remains a component diagnostic, not an official ranking result.
  Benchmark code/data revisions and CodeScaleBench's frozen suite commit are
  pinned above and in the manifest.
- Aider is an excluded challenge benchmark because it does not cleanly measure
  Wrench's bounded read-only strength.
- `run_qwen_gate_suite.py` runs the frozen binary head on When2Call and
  ToolBeHonest prior diagnostics. It records component decisions and
  allowlist checks; it does not make proposals or execute tools.
- `run_ollama_toolbehonest_baseline.py` runs a local public outside model on
  the same ToolBeHonest cases and emits paired comparison statistics against
  the saved Wrench predictions.
- `run_bfcl_irrelevance_gate.py` reproduces the prior BFCL non-live
  irrelevance diagnostic, which is not a selected scorecard.
- `run_repobench_r.py` streams all pinned RepoBench-R test shards, scores
  ContextLedger and the official Jaccard method, records per-split acc@k and
  latency, hashes inputs/predictions, and enforces the 10% RAM/VRAM reserve.
- `external/repobench-r/fetch.py` downloads only the pinned test shards. The
  data and per-case predictions stay ignored locally because the dataset
  release is marked CC-BY-NC-ND.

All run outputs and upstream checkouts stay inside this phase directory.
