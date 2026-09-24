# Training and evaluation data sources

Reviewed: 2026-09-23. This is a source-selection plan, not approval to collect,
download, train, or call a model. No dataset was downloaded and the teacher at
`localhost:4000` was not queried during this review.

## Recommendation

After explicit human approval, build the primary dataset from **opt-in,
outcome-verified Wrench workflows on participant-authorized local repository
snapshots**, supplemented by **bounded local-teacher proposals** and
deterministic fixtures. This is a future protocol choice, not permission to
capture or use real data. No training or utility corpus is admitted today. The
only admitted data are the fixed [Wrench-authored synthetic regression
fixture](../../tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json),
classified solely for open-development fixture use by the
[synthetic admission boundary](../../src/wrench_harness/synthetic_fixture_admission.py).
That classification does not admit training data or establish task utility.
The later [edge-case fixture bundle](../reports/wrench-e0-pilot-edge-cases/fixture.md)
is a separate regression test input and is not admitted to this corpus.
Keep public benchmarks as external challenge or evaluation sets unless their
exact task/repository lineage is deliberately cleared for training. Do not
start from a large general code dump.

This ordering matches the North Star: decide whether context preparation helps
real developers, and whether a small controller makes better evidence choices
than deterministic rules. A corpus of code or generated answers alone does not
measure either claim.

## Data for the North Star itself

Public market evidence is directional only. The latest results page found in
this review is the [2025 Stack Overflow Developer Survey](https://survey.stackoverflow.co/2025/ai):
66% of respondents to its frustration question reported AI answers that were
close but wrong, and 45% reported debugging generated code taking more time.
Its agent section reports substantial accuracy and privacy concerns. These
answers support asking about trust, verification and context failure; they do
not prove that users need Wrench, prefer local deployment, use the three target
clients, or will adopt a new layer. The methodology reports 49,009 responses
recruited largely through Stack Overflow-owned channels, so its own selection
limits matter. No 2026 results page was available in this review.

For actual North Star validation, collect evidence in this order:

1. **Observed last-time workflow:** ask target developers to walk through a
   recent task in OpenCode, DeepSeek Harness or Claude Code. Record the job,
   repository context they had to find, model/tool calls, context loss, retries,
   time, token/cost receipts where available, outcome and what they checked.
   Prefer screen-share or local sanitized traces over memory-only estimates.
2. **Opt-in repeated pilot:** offer a reversible local capture build to a few
   qualified developers; ask them to use it on ordinary work, review the exact
   captured data, and return after one to two weeks. Measure activation, repeat
   use, bypasses, task outcome and setup/support time. A stated intention is
   weaker than a completed install and second use.
3. **Alternative and switching evidence:** record the actual baseline tool and
   what the developer does today. Compare with Headroom and Aider on the same
   task; ask for a concrete switch/barrier and observe whether Wrench is chosen
   when both paths are available.
4. **Sustainability evidence:** measure the maintainer time for releases,
   integration support, data review and core-adapter upkeep. Ask potential
   users what support they would actually contribute (time, sponsorship,
   institutional adoption), then count only completed commitments.

Use open issue/discussion pages as a discovery queue, not prevalence evidence.
Examples found include [Cline context-continuity concerns](https://github.com/cline/cline/issues/6322),
[Aider repo-map token-budget concerns](https://github.com/Aider-AI/aider/issues/752),
and [OpenCode local-provider/context setup discussion](https://github.com/opencode-ai/opencode/discussions/256).
These are individual self-selected posts. Do not infer how common the problem
is from issue counts or feed their full text into training.

A short non-leading interview sequence:

- “Show me the last coding-agent task where finding or carrying context was
  difficult. What happened, step by step?”
- “Which evidence did the agent need, and how did you find it?”
- “Where did the agent lose or misread context? What did you do next?”
- “How did you verify the result? What happened if it was wrong?”
- “What did this cost in elapsed time, calls, usage or compute? Which receipts
  can we inspect?”
- “What information would you refuse to store or send?”
- “Which tool do you use now, and what would make you keep it instead?”
- Offer a local pilot and observe the next behavior; do not conclude from a
  hypothetical willingness-to-pay answer.

## Selective public evaluation shortlist

Choose **two** public resources for the first external context-quality check.
The primary Wrench result must still come from matched, consented Wrench
workflows; these public sets cannot prove product utility or customer demand.

| Priority | Dataset | What it tests for Wrench | Limits and use |
| --- | --- | --- | --- |
| 1 | [Agent Retrieval Bench (ARB)](https://github.com/eyuansu62/agent-retrieval-bench) | Closest match: next-file retrieval from code-to-test, review-comment-to-context, failure-trace-to-root-cause and edit-ripple signals; it includes natural no-gold and wrong-repository abstention cases. Canonical metrics include Recall@k, MRR, token-budgeted context yield and selective success. | Only 427 examples over 25 repos; Gin contributes 88/345 positive items. File-level gold is not always a correct function/span or a better completed task. Corpus content keeps each upstream repo's license. New project with a small public footprint, so pin and inspect code/release before adoption. |
| 2 | [RepoQA Search Needle Function](https://github.com/evalplus/repoqa) | Tests locating a function from a natural-language description across repositories and languages; 500 tests span 5 languages and 10 repos, with a deterministic tree-sitter similarity scorer. This adds a distinct semantic code-search query type. | It is long-context function search, not an agent trace, context-budget decision, abstention, or workflow outcome. Treat as a narrow retrieval challenge only; verify data provenance/license for each code corpus before fetching. |
| Later, if needed | [ReCUBE](https://github.com/JiseungHong/ReCUBE) | A downstream context-utility check: reconstruct a masked file from other repository files and grade it with usage-aware tests. Helps test whether repository context supports usable code, beyond file-hit metrics. | It tests reconstruction/generation more than selective context acquisition, and requires model inference plus sizable task environments. Defer until the retrieval stage has passed and data size/runtime/licensing are checked. |

### ARB release and storage gate

The benchmark authors report 427 samples across 25 repositories, four positive
workflow tracks plus two abstention strata. The corpus is 308 base-commit
snapshots, 392,000 files and 7.9 million chunks. One complete compressed
Hugging Face release archive is **441,222,815 bytes**, SHA-256
`17389762ef87795de1a5d604fc1c9a26942b3e635b3c4ce4a0f59f8d456b555b`.
The Hugging Face repository revision observed during metadata-only inspection
was `5901e1ee3aff048290db72edf9c63bc498b79ea3`. This archive's extracted peak
size was not established, and the upstream README's selective-track corpus
instructions conflict with its claim that each release bundle is self-contained.
Therefore ARB is the first benchmark to evaluate, but no download is admitted
yet. First resolve that bundle requirement, inspect exact per-subset bytes and
hashes, bound extracted plus temporary peak, check each repo license, then use
the storage checker and reserve that measured peak. Do not download all
releases by default.

ARB is also too small and repository-skewed to support a sole performance claim.
Report its tracks separately; do not average away its no-gold examples or treat
the 50 natural abstention cases as precise population-level safety evidence.
Its own published baseline reports a selective-calibration gap on those natural
no-gold examples, a useful challenge rather than a resolved abstention oracle.

### Leave these out of the first selected set

- **SWE-bench** is useful for autonomous patch success, but Wrench is a
  read-only/review-only context layer with no direct mutation authority. It is
  not a primary retrieval metric. A matched Wrench workflow replay measures
  the product end to end more faithfully.
- **Berkeley Function-Calling Leaderboard** focuses on broad function-call
  accuracy; its tool range does not match Wrench's narrow bounded schemas and
  strict abstention rules.
- **RepoBench-R** has retrieval labels for next-line completion, but is less
  agentic than ARB and its dataset card lists CC BY-NC-ND 4.0. Skip unless the
  owner explicitly accepts its separate terms after review.
- **CrossCodeEval** tests cross-file completion and could be useful if Wrench
  expands into code-completion context. It does not test an agent's next-needed
  context or abstention, so it duplicates lower-priority context utility work.
- **CodeSearchNet** is older generic docstring-to-function retrieval; its
  upstream README says the full dataset download is about 3.5 GB. It is not
  worth that footprint for this product-specific evaluation.
- **ToolBench** is broad REST API calling and explicitly marks the data for
  research/education use. It is a poor task match for the bounded Wrench
  toolset.

## Ranked sources

| Rank | Source | Best use | Reliability and limit | Decision |
| --- | --- | --- | --- | --- |
| 1 | Opt-in design-partner workflows through the intended clients, on their actual repo snapshots | Primary train/dev examples and matched E4 evaluation | Directly measures Wrench's job. Small and selection-biased; needs explicit consent, redaction, durable task IDs and outcome receipts. | Future option after human approval and participant/task opt-in. Capture only approved fields, locally by default. Ask users to mark helpful/missing evidence and task completion. |
| 2 | Local teacher at `localhost:4000`, reported by the owner as available for local use | Propose alternative evidence rankings, retrieve/stop decisions, task strata, hard negatives and concise explanations for review | Candidate labels can be confidently wrong, self-consistent, or biased toward the teacher's style. Teacher use does not turn outputs into truth or remove compute/storage limits. | Future option only on approved snapshots and permitted uses. Record actual model identity/revision, request settings, snapshot and prompt hashes. Deterministic checks and blinded human adjudication decide admission. Never retain hidden chain-of-thought. |
| 3 | Exact local or synthetic fixtures with authored oracles | Boundary, parser, retrieval, abstention, stale-handle, prompt-injection and failure tests | Excellent repeatability and exact expected actions; weak evidence of user frequency or real-world value. | Keep separate from real traces. Use for zero-tolerance safety and regression gates, not utility prevalence claims. |
| 4 | [Stack Overflow Developer Survey](https://survey.stackoverflow.co/2025/ai) | Market/problem context and interview prompts | 2025 survey of 49,009 responses, with self-selection through Stack Overflow channels. Useful for broad directional context, not a sample of Wrench's target users or proof of buying/adoption. | Cite its method and date; use to shape questions, never to substitute for target-user interviews. |
| 5 | Public issue/PR discussions in OpenCode, Aider, Cline and similar projects | Discover terminology, setup failures, context complaints, integration requirements and candidate interview questions | Public posts are anecdotal, self-selected and may include personal or confidential details. They do not establish incidence or license for model training. | Manually code a small, linked, minimized sample for qualitative discovery. Do not ingest comments wholesale or treat counts as market size. |

## Local teacher data protocol

Use the teacher as a **candidate generator** for bounded fields, not as an oracle.
A candidate record may contain: task category; ranked repository evidence IDs;
selected/omitted IDs; `ENOUGH` or `RETRIEVE_MORE`; permitted namespace; route
choice; expected abstention class; and a short evidence-based justification.
Exclude hidden reasoning, secrets, raw credentials, unredacted private code,
and unrelated conversation.

For every generated candidate, bind the record to:

- Consent and source authorization, repository and task-group identifiers,
  source snapshot hash, timestamp and redaction/review state.
- Teacher product/model/revision as returned by the local server, endpoint
  configuration, prompt/template hash, decoding settings and output hash.
- Candidate evidence IDs and spans, deterministic tool receipts, expected
  action/abstention oracle, reviewer decision and eventual task outcome.
- Dataset split and parent lineage, so derivatives inherit exclusions and
  cannot cross from sealed evaluation back into training.

Generate examples only from admitted training/dev snapshots. A judge model can
rank or explain candidates, but acceptance needs independent evidence: exact
scripted oracle, test result, source-range verification or human review. Do not
ask the same teacher to both generate and certify a label. Preserve disagreement
as `unresolved`; never force a binary label to increase corpus size.

The owner reports unlimited local teacher usage. This means no per-request
provider spend is expected; it does not establish model identity, output
quality, consent for source data, or unlimited RAM/VRAM/disk/throughput. Before
any teacher-data job, check the 50 GB budget, reserve peak storage, inspect live
RAM/VRAM and bound request count, output bytes, logs and temporary copies.
Store generated data under the approved data root with hashes and a manifest.

## Evaluation set construction

The primary evaluation should be a new, consented and frozen real-workflow
replay set with tasks sampled across localization, failed-test/log triage,
context restoration, relevant-tool/schema choice, risky/out-of-scope abstention,
and difficult retrieval cases. Sample from more than one repository, language,
and task family. Estimate sample size from paired outcome variance and the
predeclared non-inferiority/improvement margins; do not choose a convenient
count and claim significance.

Freeze repository snapshot, task, prompt, rules, all four arms, downstream
model, teacher identity (if used to produce candidate labels), token accounting,
oracles and stopping criteria before running. Compare:

1. Downstream teacher/strong model alone.
2. Deterministic Wrench plus the same downstream fallback.
3. Deterministic Wrench plus foundation and frozen Wrench-Core controller.
4. The same as arm 3 plus a personal adapter fit only on prior permitted data.

Keep splits separated by repository/fork, task family and time. A repo, near-
duplicate, generated paraphrase, teacher answer, or derived trajectory must
inherit the original task's split. Seal the final set, log all access, and
exclude any exposed item honestly. Report task success, eligible correct
accepts, correct abstentions, prohibited accepts, paired uncertainty, full
latency/tokens/cost and local resource use. Benchmark scores are secondary to
matched workflow outcomes.

## License, privacy and leakage gates

- Public visibility is not blanket training permission. GitHub's API terms
  apply to API use and impose rate limits; repository files can have distinct
  licenses. Store repository revision and license evidence for every public
  source. Unlicensed/unknown or incompatible content is not admitted by
  default.
- Stack Exchange user contributions have CC BY-SA terms that vary by post
  date. The public data dump is not a frictionless input for proprietary-style
  weight fitting; seek a documented rights review before any such use.
- Public issue/patch benchmarks can appear in model pretraining or teacher
  training. Keep public benchmark evaluation quarantined and label possible
  contamination; a local teacher does not remove this risk.
- Design-partner traces require informed opt-in, clear use/retention choices,
  redaction, deletion/reset and no capture of secrets. Keep private repo data
  local unless a specific transfer is authorized.
- Maintain a source ledger with URL/revision, exact license or consent basis,
  collection date, hashes, permitted use, split, transformations and deletion
  status. No dataset is admitted on its name alone.

## First data pilot

Do not download a public corpus or collect real tasks under this plan. For
offline work, use authored deterministic fixtures only. After a separate human
approval of consent, permitted use, capture, retention, withdrawal, deletion,
and source access, a future pilot may add opt-in local tasks and bounded
teacher-generated candidate rankings. Keep any approved pilot examples in
development only; build a separate repository/time holdout before a training
comparison. Make no utility claim from a small pilot. Its decision is whether
capture, label review, and source lineage work reliably enough to propose a
powered E0/E1 replay.

## Sources checked

- [Agent Retrieval Bench paper](https://arxiv.org/abs/2607.24882), [repository and metrics](https://github.com/eyuansu62/agent-retrieval-bench), [data licensing notes](https://github.com/eyuansu62/agent-retrieval-bench/blob/main/DATA_LICENSE.md), and a read-only [Hugging Face file-size/hash API](https://huggingface.co/api/datasets/eyuansu71/agent_retrieval_bench?blobs=true) support the new first choice.
- [RepoQA repository](https://github.com/evalplus/repoqa) describes its 500-case Search Needle Function suite and deterministic syntax-similarity scorer.
- [ReCUBE paper](https://arxiv.org/abs/2603.25770) and [release repository](https://github.com/JiseungHong/ReCUBE) describe the downstream context-utilization option.
- [SWE-bench FAQ and dataset descriptions](https://www.swebench.com/SWE-bench/faq/)
  describe issue/patch instances, engineer verification and test-based grading.
- [RepoBench repository](https://github.com/Leolty/repobench) describes
  cross-file retrieval/completion subtasks and separate language snapshots.
- [CodeSearchNet repository](https://github.com/github/CodeSearchNet) describes
  two million docstring/function pairs, repository-separated splits and a
  3.5 GB download. It is an older generic code-search resource; its size and
  weak match make it a low-priority baseline, not a Wrench trace corpus.
- [BFCL](https://gorilla.cs.berkeley.edu/leaderboard) evaluates function calls;
  its breadth is useful as a challenge set but not as Wrench's tool authority
  oracle.
- [ToolBench](https://github.com/OpenBMB/ToolBench) reports 126,486 generated
  examples over 16,464 RapidAPI functions and says the data is research and
  educational use only. This broad REST API corpus has poor task fit; skip it
  for Wrench training.
- [Stack Overflow survey methodology](https://survey.stackoverflow.co/2025/methodology)
  documents recruitment and self-selection limits. [Content license guidance](https://stackoverflow.com/help/licensing)
  documents CC BY-SA versions for community posts.
- [GitHub API rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
  and [GitHub Terms, API and AI sections](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service)
  are required reading before collection or training use.
- [SWE-agent trajectory format](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/trajectories.md)
  can inform a compact action/observation receipt format. Do not ingest its
  trajectories without separate rights, task-overlap and provenance review.

This is a research shortlist, not legal advice or a dataset acquisition
approval. No external service was contacted beyond reading public source pages.
