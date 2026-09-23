# Goal: Wrench productive value

Status: active
Updated: 2026-09-23
Owner: repository agent, under human product authority

## Product mission and hardware direction

Human product direction, clarified 2026-09-22: **affordable AI for the rest
of us**, using hardware people already own and aiming to make the software
free to use.

- Initial audience: people with less than 8 GB of GPU memory.
- Next hardware milestone: make a useful bounded workflow work well with
  less than 2 GB of GPU memory, and investigate older phones as a related
  device target. Phone shared memory is not equivalent to discrete GPU VRAM.
- Longer-term vision: let friends voluntarily lend one another spare compute.

These are product targets, not verified compatibility or shipped features.
The current bounded developer-tool worker is the first delivery slice. Its
paired workflow and safety gates remain in force. Hardware claims must name
the actual device, available memory, workload, correctness, latency, and
resource use. Phone feasibility must also account for sustained operation,
battery, and thermal limits. Shared compute needs its own consent, data-access,
and revocation design before implementation or promotion as an available tool.
This direction does not automatically restart the archived model, adapter,
remote-worker, or packaging experiments listed below.

## Product outcome

Deliver a trustworthy, bounded Wrench worker that creates measurable value on
routine developer-tool work. The immediate delivery gate is productive
workflow value; broader hardware milestones follow from that useful slice.

Wrench handles fast, repetitive, verifiable mechanical work. It proposes
structured read-only or review-only actions, or abstains. An independent
verifier and the stronger-model fallback retain final authority. Wrench never
executes arbitrary shell commands, accesses credentials, or writes
autonomously.

## North Star

The North Star is one paired real-workflow canary:

1. run the same authorized workload through the stronger-model baseline;
2. run it through the Wrench hybrid path with the same fallback, verifier,
   retry, and correction policy;
3. reconcile final success, safety, latency, frontier tokens, local tokens,
   cost, retries, corrections, abstentions, and fallback overhead.

The paired canary is necessary but not sufficient. Final acceptance must also
meet all five release gates in the active utility contract, including the
three-arm replay and weighted-workload coverage requirements.

The canary must show no material final-success or safety regression, zero
prohibited accepts, zero unexpected mutations, meaningful end-to-end latency
improvement on successful eligible tasks, and at least 95% net frontier-token
savings after compaction, verification, retries, corrections, and fallback.

Synthetic replay, an HTTP success, a client smoke, a smaller checkpoint, or a
lower teacher-call count is not North Star evidence by itself.

## Keep and continue

These are the active workstreams. The scoped binary-model addition below was
authorized by the human product owner in this conversation on 2026-09-22.

1. **Deterministic mechanical worker**

   Fast, bounded handling of routine developer-tool work.
2. **Independent verifier and no-mutation boundary**

   Every proposal remains schema-checked, permission-checked, and fail-closed.
3. **Hybrid long-context intake and retrieval**

   Accept large raw context, retrieve the relevant evidence, and compact model
   work into a bounded working context.
4. **Two-state client protocol**

   Use a bounded proposal followed by a hash-bound final answer after a
   verified read-only result. No repeated or unbounded tool loop.
5. **OpenCode, DeepSeek Harness, and Claude Code support**

   Keep these three bounded client surfaces working. Do not add more clients
   without demonstrated user demand.
6. **Latency and timeout repair**

   Remove avoidable timeout and queueing outliers from the successful path.
7. **One paired real-workflow canary**

   Measure actual productive value against the stronger-model baseline.
8. **Targeted fallback expansion**

   Add only deterministic, verifier-friendly handlers justified by real
   fallback volume after the canary.
9. **Sustained operational testing**

   Exercise concurrency, cancellation, timeouts, recovery, circuit breaking,
   accounting, and no-mutation behavior over sustained local operation.
10. **Binary System One readout on the existing Qwen weights**

   Human direction: "we want a super light weight abstain or not abstain"
   and "system 1 model", then clarified: "we already got qwen's weights,
   we need to turn it into system 1 style output to determine abstain or
   not abstain". This supersedes both broad OpenJev parity and the separate
   lexical classifier experiment. Reuse the existing frozen Qwen backbone
   and train a small two-output head. Classification must use one text
   backbone forward without vocabulary projection or autoregressive decoding.
   Its only decisions are `abstain` and `not_abstain`; the latter merely
   continues to the existing proposal/verifier path. It grants no execution
   authority. Training and local evaluation for this bounded model are now
   authorized, with the existing 10% RAM/VRAM reserves. No OpenJev weights,
   paid model calls, remote worker work, or production enablement are included.
   Use an additional head artifact under 1 MiB. The earlier <=5 ms total
   latency target belonged to the superseded standalone lexical model;
   reusing Qwen still incurs a backbone forward. Measure complete warm
   classification latency including tokenization and GPU synchronization,
   and report existing backbone memory separately from added head size.
   Record held-out eligibility coverage, unsafe misses, checkpoint and head
   identity, exact input limits, and integration evidence.
   Authored examples establish an experimental checkpoint only; independent
   real-workflow usefulness and the existing release gates remain required.
   Keep the existing final evaluation split out of training and tuning.
   Implementation status: [Qwen binary System One](phases/qwen-system-one-20260922/README.md).
   The user subsequently prioritized binary decision **speed and accuracy**,
   compared with Jev/OpenJev's published metrics. Report actual classifier
   latency and correct abstain/not_abstain labels, with denominators and
   hardware. Keep published cross-dataset comparisons distinct from parity.
   New work and source references are in
   [System One classifier readiness](phases/system-one-readiness-20260922/README.md).
   The fixed-policy candidate scored 36/60 on a fresh independent binary set,
   with seven unsafe classifier continuations; the original head scored 37/60
   with thirteen. Both failed the local accuracy target. Its binary rule was
   fixed at 0.5 before evaluation. 90 CPU implementation contracts pass,
   including the small MLP and sparse readouts. The owner then requested at least
   5,000 realistic abstain cases and continued training until the Wrench-or-
   abstain classifier achieves high accuracy. A generated, repository-grounded
   diagnostic suite now contains 5,000 abstain cases and 600 eligible Wrench
   controls, kept out of training. A later audit found incorrect positive
   file-size labels in the training expansion, so its MLP and sparse-head
   calibration figures are superseded. The first frozen
   5,600-case suite run with a Qwen plus sparse readout scored 72.39% overall,
   73.76% balanced, with 1,399 false Wrench decisions. Warm p50/p95 was
   175.86/228.54 ms on RTX 5070 Ti. Its predeclared diagnostic target failed.
   A second sparse candidate's training data contained invalid positive file
   bounds, so its calibration result is superseded. A corrected training set
   has passed structural file and bounds checks, with human label review pending.
   Its head scored 78.80% overall and 75.30% balanced accuracy on a replay of
   the consumed 5,600-case suite, with 1,012 false Wrench decisions. An optional
   preflight improved abstain recall to 91.02% but still left 449 false Wrench
   decisions and 175 missed Wrench controls in a posthoc same-suite analysis.
   A layer-8 readout improved balanced accuracy to 79.18% at 148.62/185.13 ms
   warm p50/p95 on the consumed suite; a posthoc preflight overlay reached
   84.89% balanced accuracy, with 469 false Wrench decisions. It also failed
   the diagnostic target. Further synthetic template fitting is not adequate
   evidence for production; real labeled Wrench requests are the next input.
   Production and Jev parity remain unproven.
   The owner subsequently approved using the original 5,000-abstain authored
   suite for training. It is now retired as evaluation for new heads. A
   layer-8 head was fitted on 6,528 rows and scored once on a fresh authored
   5,000-abstain plus 600-control replacement. First-pass accuracy was 98.04%
   overall, 96.70% balanced, with 80 unsafe continuations and 30 false
   abstentions at 170.33/223.15 ms warm median/p95. The target failed.
   A revised abstain-only preflight removes those 80 in a posthoc regression
   of the consumed suite; that is not a fresh pass. Human label review and
   real-workflow validation are still absent. The evidence and frozen head
   are in [owner-approved training](phases/system-one-authorized-training-20260923/README.md).

11. **Benchmark-led model improvement against outside models**

   Human direction, 2026-09-23: build a dedicated evaluation phase with five
   scorecards, one internal and four external, and use the measured gaps to
   improve Wrench in its bounded read-only developer-tool categories. The
   primary comparison target is Qwen3.5 9B on frozen, case-matched tasks;
   Qwen3.5 27B is a stretch target. The selected external suites are Agent
   Retrieval Bench V2 (fixed-budget repository retrieval), CodeScaleBench
   (paired downstream workflow impact), SWE-Explore-Bench (ranked file/line
   exploration), and ContextBench (coding-agent context quality). These four
   have clear public metrics and outside-model/system references while staying
   closest to Wrench's read-only authority. Keep every dataset pin, adapter,
   run, metric, and comparison receipt in
   [the dedicated benchmark phase](phases/phase-446-agent-benchmark-fit/README.md).
   The current model-gap evidence and next candidate protocol are in
   [the model improvement plan](phases/phase-446-agent-benchmark-fit/MODEL_IMPROVEMENT_PLAN.md).
   Make the target falsifiable by predeclaring primary metrics and reporting
   paired uncertainty. A published leaderboard result is a reference only
   until Wrench and the outside model use the same tasks, prompts, harness,
   budgets, and scoring path. Report every selected result, including negative
   results. Do not tune against the sealed final split or claim superiority
   from mismatched published numbers. Preserve the Wrench verifier and
   read-only authority boundary. Paid provider calls, production enablement,
   and changes to unrelated skipped workstreams are not authorized by this
   evaluation direction.

12. **Owner-directed 20,000-row Wrench training corpus**

   Human direction, 2026-09-23: prepare exactly 20,000 quality-screened
   training records for the six allowlisted actions and their abstention or
   fallback boundaries. Keep evaluation records outside this training count.
   For a healthy 80/10/10 split, add 2,500 development/calibration and 2,500
   sealed final evaluation records, for 25,000 total examples. Use a balanced
   per-action floor, then allocate the traffic-weighted portion using
   reviewed, redacted real workflow frequency and measured practical value,
   including frontier-token mass, verifier success, and final task outcomes.
   Do not invent production frequencies from synthetic examples. The initial
   training design reserves 7,200 balanced action and matched-boundary
   examples, 9,600 examples allocated from observed high-value workflow
   traffic, and 3,200 out-of-scope or escalation examples across four boundary
   families. If approved real traces do not support the traffic-weighted
   allocation, record the shortfall rather than padding it with near-duplicate
   prompts. Four thousand evaluation records outside 20,000 training records
   would be 16.7% of the 24,000-row combined set, not 20%.

   Every training row must have source and license or consent status, an
   action family, a task/template group, a verifiable expected action or
   abstention reason, label-review provenance, and duplicate-screening
   results. Synthetic examples remain quarantined until human label review.
   Do not train from `final.jsonl` or any sealed evaluation split. Do not use
   the external general tool-call bundle, which has been removed from the
   active corpus and archived on D: because task-fit failed and licensing is
   still pending. Reconsider it only if both task-fit and licensing are
   approved. Keep large corpus files under
   `D:\\wrench-slm-data`; keep manifests, validators, and concise receipts in
   the repository. Do not start a new fit until the corpus audit and split
   separation pass. This data-preparation work does not authorize production
   enablement or changes to Wrench's tool authority.
   The current inventory and proposed quality gates are in
   [the 20,000-row corpus plan](phases/phase-447-wrench-training-data-corpus/README.md).

## Explicitly skipped

The following are archived or paused and must not become active work without a
new human product decision:

- RTX 5060 Ti verification;
- private release packaging as a separate workstream;
- learned free-form routing and LoRA optimization beyond the explicitly
  authorized tiny binary classifier above;
- dense-native 4M attention;
- stock Ollama, vLLM, and GGUF adapter work;
- additional synthetic replay work as a primary milestone;
- broad speculative tool expansion;
- public production release before the North Star canary and operational
  evidence pass.

## Active product boundary

The active serving path is model-local hybrid execution:

1. accept the raw request at the Wrench endpoint;
2. use deterministic retrieval, search, AST or dependency extraction where
   applicable;
3. preserve current intent and hash-bound evidence;
4. compact model work to a bounded working context;
5. emit a typed proposal or abstention;
6. independently verify it;
7. execute only bounded read-only or review-only work;
8. return a hash-bound final answer or the original request to the stronger
   fallback.

The large-context intake is a hybrid retrieval capability. It is not a claim
of dense-native 2M or 4M decoder quality.

## Active acceptance gates

- **Gate A, Proposal Semantics:** zero schema errors; eligible cases match
  typed oracles; out-of-boundary cases match exact expected abstention reasons.
- **Gate B, Verifier and Authority Bounds:** zero prohibited accepts. Any
  unexpected side effect or unverified boundary escape is an immediate
  `FAIL_WRENCH`.
- **Gate C, Model Comparison versus Full-Expert Teacher:** final task success
  and safety must not materially regress against teacher-only execution.
  Report eligible-task correct acceptance and overall correct outcomes with
  paired 95% confidence intervals. Median and p95 end-to-end latency must
  improve by at least 50% on successful eligible tasks. Fast refusals do not
  count as fast completion.
- **Gate D, Matched Real-Workflow Utility:** replay matched traces across
  stronger-model-only, rules-plus-fallback, and Wrench-plus-fallback arms.
  Cover at least 90% of weighted mechanical-workload frontier-token mass and
  achieve at least 95% net frontier-token savings after local inference,
  verification, compaction, retries, corrections, and fallback overhead, with
  zero material final-success regression.
- **Gate E, Operational and Operational Shadow:** demonstrate robustness under
  concurrency, cancellation, timeout, and circuit breaking through
  `ProposalRouter`.
- **Client protocol:** OpenCode, DeepSeek Harness, and Claude Code each complete
  the bounded two-state proposal, verification, and hash-bound final-answer
  flow without free-form execution or repeated proposal loops.
- **Targeted expansion:** add a handler only when real traces show material
  fallback value and an independent verifier can bound its authority.

Missing evidence is inconclusive, not a pass. Final acceptance, promotion,
publication, deployment, and spending remain human decisions.

## Source of truth

- [GOAL.md](GOAL.md) is the active product goal and North Star.
- [COLLABORATION_CONTRACT.json](COLLABORATION_CONTRACT.json) is the active
  machine-readable Q4 authority contract.
- [WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md](docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md)
  is the active productive-value evidence contract.
- [WRENCH_LONG_CONTEXT_SERVING_CONTRACT.md](docs/WRENCH_LONG_CONTEXT_SERVING_CONTRACT.md)
  records the active hybrid serving boundary.
- [AGENTS.md](AGENTS.md) provides repository and host safety rules. The
  ignored `AGENTS.local.md` file contains historical worker-queue procedures
  and is not part of the active contract.
- [docs/evidence/GOAL_HISTORY_2026-09-22.md](docs/evidence/GOAL_HISTORY_2026-09-22.md)
  and [docs/archive/2026-09-22/](docs/archive/2026-09-22/) preserve superseded
  plans and historical evidence. They are not active instructions.

## Current status

The deterministic worker, independent verifier, hybrid intake, bounded
two-state protocol, and three named clients have local evidence. The `200/200`
operational shadow covers the portable server's mechanical-only path, not
`ProposalRouter` in the serving lifecycle. Phase 428 contains Windows client
subprocesses on timeout, but this does not establish serving-path resilience or
latency improvement.

The paired client runner now checks the saved final answer on both arms. A
re-audit of the older Phase 389 capture found that OpenCode exited zero without
the expected heading. The isolated pinned 1.18.32 follow-up returned the
expected direct answers and all three hybrid client answers. These local
fixture checks do not establish real-workflow parity or latency. See the
[saved-answer audit](phases/canary-answer-audit-20260922/README.md) and the
[pinned-client follow-up](phases/opencode-output-diagnosis-20260922/README.md).

**Release state: not ready.** Gates C and D remain open: there is no adequate
matched teacher comparison with paired confidence intervals and latency
distributions, and no complete three-arm replay with weighted coverage and
verified net savings. The approved test-only `ProposalRouter` path now runs
through the actual HTTP handler with deterministic child callbacks. Its focused
and combined server/router tests pass, including concurrent successes and
failures, exact circuit-threshold enforcement, invocation failure, abrupt
fake-child exit and router reset, cancellation, deadline termination, trace
accounting, and worker cleanup.
This bounded fixture does not establish sustained or
production-path resilience, so Gate E remains open. Gates A and B have local
implementation and test evidence, but this active record does not claim their
release acceptance. Phase 438 hardens schema-v1 router-state restoration and
tests open-circuit and operator-bypass preservation across router
reconstruction. This validates the persistence helper only, not model-worker
process restart or serving-state persistence. Phase 439 adds explicit support
for OpenAI daily aggregate cost evidence while retaining provider request-row
evidence, and upgrades paid-canary preflight to schema-v3 child contracts that
bind the accounting source and required isolation/headroom evidence. Local
tests do not establish a live project, cap, export, or route identity. The
Phase 440 inspection confirms router-state recovery is helper-level only. Its
proposed loopback test-server persistence change awaits a separate Q4 decision
and has not been implemented. The bounded `minimax-guided`
experiment passed its one-case answer oracles and captured `63,354` frontier
tokens, but returned no provider cost. The `$0.0191988` configured-rate
estimate is not a paid-cost receipt. Session-title calls are auxiliary traffic
and must be counted in any paired comparison. The approved test-only Gate E implementation and its
limits are in [Phase 434](phases/phase-434-router-serving-path/README.md).
Shutdown regression coverage also confirms handler and server cleanup cannot
double-join or double-close an in-flight fake child.
Phase 441 adds fail-closed validation for malformed results from the injected
test-only callback: unknown statuses and abstentions without a reason are
normalized to a canonical abstention, counted as router failures, and tested
to open the circuit. Its focused server/router regression passes 43 tests with
Ruff clean. This closes the malformed-callback defect only; it does not close
Gate E or change production readiness. See
[Phase 441](phases/phase-441-router-malformed-callback/README.md).
Phase 443 reproduced a separate canary authorization gap: a synthetic MiniMax
child passed under the then-active GPT-6 parent because child route identity
was not compared with a structured parent allowance. On 2026-09-22 the human
approved the fail-closed guard and selected OpenRouter MiniMax M3 as the
comparison route. Phase 444 records the route-bound parent contract and
validator tests. This closes only the authorization mismatch, not the
remaining paid-canary prerequisites or any release gate. No provider request
was made. See [Phase 443](phases/phase-443-parent-route-binding/README.md) and
the active [Q4 route allowance](COLLABORATION_CONTRACT.json).
Phase 435 attempt 01 stopped after one nonaccepted response: 28 of 29 started
requests passed, with no surviving child and safe RAM/VRAM reserves. Attempt
02 captured 27 accepted responses and two `router_queue_timeout` failures,
again with no child leak and safe reserves. The one approved retry was run
with the old five-second proposal and 12-second HTTP timeouts because the
runner ignored `--help` and started immediately. It therefore did not test the
approved 20/30-second settings, and that approval was consumed. The runner now
uses those settings and requires `--run`; help/default invocation are
non-running. Six focused tests cover metadata capture, receipt preservation,
and the no-implicit-run guard. On 2026-09-22 the human gave fresh Q4 approval
for exactly one corrected loopback fake-callback run. Attempt 03 passed all
200 requests in 54.527 seconds using the approved 20/30-second settings, with
no callback failures, child leaks, or reserve breaches. It made no
provider/model calls. This bounded fixture evidence does not close Gate E or
authorize production routing or another soak. See
[Phase 435](phases/phase-435-router-soak/README.md).

Phase 433 closed the configured-loopback authorization bypass and recorded a
fresh local three-client regression, still inconclusive for accounting. This
turn's full suite passed `324` tests with `18` existing Windows asyncio
deprecation warnings. Q4 contract validation returned `VALID`. The human
approved exactly one paid paired canary, one repetition, with a `$500` maximum,
and clarified that the current loopback gateway route is GPT-6. The active Q4
parent now records that ceiling and the one-canary scope. This is not itself a
provider-enforced cap. Phase 436 binds child approval to the active parent hash
and rejects a child cap above the parent budget before output or network
activity. Phase 437 also requires a child-bound expected provider model and
rejects paid-cost receipts whose reported model or charge differs from the
approved child. Read-only gateway metadata confirms the registered alias
`current` maps to `openai/current` and reports OpenAI ownership, but does not
resolve that alias to GPT-6. The user's clarification specifies the GPT-6
family, but not the Sol, Astra, or Luna variant.
The provider-enforced cap reference and authenticated cost-export access
remain unverified.
The official OpenAI Costs endpoint is now identified, but its daily aggregate
shape does not contain request IDs, request token usage, or provider-model
identity. No paid request was made. See
[Phase 433](phases/phase-433-paid-loopback-child-guard/README.md) and
[Phase 436](phases/phase-436-parent-budget-and-route-binding/README.md) and
[Phase 437](phases/phase-437-paid-cost-cap-validation/README.md) and
[Phase 439](phases/phase-439-openai-cost-export-compatibility/README.md). The next
release evidence must come from the correctly identified paired canary, the
broader operational Gate E evidence, and the required three-arm replay, not
another synthetic score. The human clarified that the intended service on port
4000 is GPT-6, not MiniMax. Phase 439's read-only API receipt identifies three
configured GPT-6 aliases, Sol, Astra, and Luna, while `current` remains
`openai/current` with display name `Current model`. The intended variant awaits
human selection; no model completion request was made. Phase 403 remains
historical MiniMax evidence.

Phases 419-432 hardened request attribution, two-state validation, canary
accounting, and workload coverage. Their deterministic local receipts do not
establish provider cost or close Gates C and D. Detailed findings remain in
the per-phase reports and historical archive.

Learned routing remains disabled. The project is active and evidence-gated,
not approved for production enablement.

## Q4 collaboration contract

This goal is `CHALLENGE` because productive value, safety, release scope, and
workflow comparison combine high consequence risk with uncertainty and
reasonable expert disagreement. Human initiative, acceptance, and commit
authority remain explicit.

| Task class | Mode | Boundary |
| --- | --- | --- |
| Read-only inspection, documentation edits, deterministic local tests, and reversible evidence indexing | `AUTO` | Repository-only, with diff and test verification |
| Sustained local operational testing and bounded real-client canary preparation | `GUARD` | Stop before external effect, spending, or promotion |
| Product wording, tradeoffs, and interpretation of canary value | `COCREATE` | Human acceptance and final commit |
| Workflow comparison, fallback expansion, routing, and architecture changes | `CHALLENGE` | Human decision with AI evidence, alternatives, and dissent |
| Production enablement, deployment, publication, credential approval, or unverified safety judgment | `HUMAN_ONLY` | Human performs or explicitly takes over |

Human owns product intent, scope, acceptance, promotion, publication,
deployment, provider spending, and release decisions. The agent may inspect,
implement, test, and collect evidence only inside the repository and approved
redacted inputs. Human timeout means stop and preserve state.

Every consequential experiment records source, artifact, runtime, verifier,
prompt, workload, resource, accounting, failure, and rollback identity. Any
verifier failure, scope expansion, permission expansion, budget overrun,
security or privacy concern, unbounded retry, or unresolved disagreement
escalates to the human.

## Builder execution record

Updated: 2026-09-23

### Progress and validation

- Phase 446 benchmark slate has five total scorecards: one internal paired
  workflow-utility scorecard and four external suites selected for fixed-budget
  repository retrieval (ARB V2), paired workflow impact (CodeScaleBench),
  ranked file/line exploration (SWE-Explore-Bench), and coding-agent context
  quality (ContextBench). The external evaluators publish clear metrics and
  outside-model/system references; published rows remain reference-only until
  same-task, same-interface reruns. ARB V2 is the strongest current external
  result: the Wrench BM25 component gained BCY@8K with a paired positive
  interval, while remaining below published Qwen embedding references. The
  latest V5 gate comparison is diagnostic, not valid primary evidence: the
  internal labels treated requests for untracked Git paths as eligible even
  though the executor omits them. Corrected V6 was low-coverage (54/80,
  6/32 eligible accepted, zero unsafe). V7 trained from a fresh tracked-scope
  calibration and development split with explicit executor capability text.
  On the original system prompt, V7 scored 58/80 with 10/32 eligible accepted
  and zero unsafe continuations. Qwen3.5 9B scored 67/80 with 27/32 eligible
  accepted and 8 unsafe continuations; its paired accuracy interval versus
  Wrench includes zero. Qwen3.5 27B scored 80/80, 32/32 eligible, and zero
  unsafe; its paired accuracy lead over Wrench is 27.5 points (95% CI
  [+18.75, +36.25]). Wrench is substantially faster but has a large coverage
  gap, so this is not a quality or utility win. V5 does not count as primary
  evidence. The selected external slate is fit-first and keeps weak results
  visible. SWE-Explore and ContextBench pre-BM25 runs remain in progress. See
  [Phase 446](phases/phase-446-agent-benchmark-fit/README.md) for the oracle
  audit, selection rationale, and current evidence.

- Latest full regression after Phase 441: 341 passed with 18 existing Windows
  asyncio deprecation warnings. Phase 439's focused validator and canary
  preflight suites pass 66 tests. Phase 441's focused server/router regression
  passes 43 tests, and Ruff passes on its changed Python files.
- Phases 419-432 improved client attribution, two-state answer checks, accounting provenance, and workload coverage. These local and diagnostic receipts do not establish provider cost or close Gates C and D.
- Phases 391-392 passed the mechanical-only 200-request shadow. Phase 434 added test-only `ProposalRouter` serving-path coverage; Phase 435 attempt 03 passed its bounded fake-callback soak, without closing Gate E.
- Phase reports preserve the details and failed attempts. Historical turn-by-turn evidence remains in [the evidence archive](docs/evidence/README.md).

### Current evidence

- [Phase 391-392 operational shadow](phases/phase-391-sustained-operational-shadow/README.md) records 200/200 mechanical-only requests. It does not exercise `ProposalRouter`.
- [Phase 411 routing review](phases/phase-411-router-gate-advisor/README.md) identifies the serving-path gap; the approved test-only integration is in [Phase 434](phases/phase-434-router-serving-path/README.md).
- [Phases 419-424 client attribution and protocol](phases/phase-419-direct-call-attribution/README.md) preserve local client-window, task-state, and exact-answer evidence. They do not establish paid route accounting.
- [Phases 425-432 canary and coverage guards](phases/phase-425-canary-status-semantics/README.md) keep incomplete comparisons inconclusive and reject missing workload mass.
- [Phases 427-429 Windows process containment](phases/phase-427-subprocess-tree-timeout/README.md) record client cleanup evidence, not server-worker resilience.
- [Phase 433 paid-loopback guard](phases/phase-433-paid-loopback-child-guard/README.md) preserves the pre-approval zero-spend guard; Phase 437 records the later one-canary `$500` Q4 ceiling and its remaining prerequisites.
- [Phase 435 router soak](phases/phase-435-router-soak/README.md) records two failed attempts and one corrected 200/200 loopback fake-callback pass. The fresh one-run Q4 approval is consumed; no provider/model calls or further soak are authorized.
- [Phase 438 router-state recovery](phases/phase-438-router-state-recovery/README.md)
  rejects inconsistent persisted counters, circuit flags, and bypass state,
  and verifies open-circuit and operator-bypass preservation across helper
  reconstruction. It does not establish model-worker or serving-process
  restart recovery.
- [Phase 436 parent-budget guard](phases/phase-436-parent-budget-and-route-binding/README.md) requires a child approval to bind the exact parent contract hash, rejects spend caps beyond the active Q4 budget, and records parent authorization in receipts. The $500 ceiling remains; the active Q4 parent contract records the later MiniMax route choice and exact binding. Provider dispatch and cost accounting remain unverified.
- [Phase 437 paid-cost cap and provider-model binding](phases/phase-437-paid-cost-cap-validation/README.md) binds the gateway alias and expected provider model separately in the child contract, enforces the child cap, and requires export rows to match the receipt. It does not prove alias dispatch or export authenticity.
- [Phase 439 OpenAI aggregate-cost compatibility](phases/phase-439-openai-cost-export-compatibility/README.md) adds native daily aggregate evidence with exact project/key, bucket, isolation, and spend-headroom bindings. It does not prove API access, source authenticity, provider dispatch, or hard-cap enforcement.
- [Phase 440 router restart-state decision](phases/phase-440-router-server-restart-state/README.md) confirms 24 focused helper/serving tests pass, but server-process state recovery is unproven. A test-only loopback persistence design is awaiting Q4 human choice; no server lifecycle changes have been made.
- [Phase 441 malformed callback regression](phases/phase-441-router-malformed-callback/README.md) verifies invalid test-only callback results fail closed through the router circuit. It does not exercise the model worker or close Gate E.
- [Phase 442 MiniMax/OpenRouter credential check](phases/phase-442-minimax-openrouter-credential-check/README.md) confirms both gateway aliases and read-only credential acceptance. It is not a model-completion, cost-export, or provider-cap test.
- [Phase 443 parent-route binding review](phases/phase-443-parent-route-binding/README.md) records the synthetic route mismatch and Sol's guard recommendation. The active [Q4 parent contract](COLLABORATION_CONTRACT.json) records the human route choice and binds the one-canary scope to OpenRouter MiniMax M3. Local canary and paid-receipt validators reject missing or mismatched child routes. This is authorization evidence only; no provider call was made.
- [Current client-output audit](phases/opencode-output-diagnosis-20260922/README.md) records the pinned OpenCode repair and remaining direct-baseline/accounting gaps.
- [Phase 448 paired-canary trace-source audit](phases/phase-448-paired-canary-trace-source-audit/README.md) correlates all 397 capture IDs with event logs and recovers partial request/token/latency accounting. It still lacks consent provenance, independently reviewed redaction, task-verifier outcomes, complete joins, and provider costs, so it is only a candidate workload source and does not close Gates C or D.
- [Phase 449 context-client abstention](phases/phase-449-context-client-abstention/README.md) records a narrow fix for a missing-user `IndexError` in context retrieval. It has not been exercised by tests and does not close Gate A or Gate E.
- [Phase 450 Git status config isolation](phases/phase-450-git-status-config-isolation/README.md) disables repository-configured FSMonitor commands for the bounded `git_read_status` call. The change has not been regression-tested and does not establish Gate B.
- [Phase 451 search fallback containment](phases/phase-451-search-fallback-symlink-containment/README.md) resolves and confines Python fallback search targets before reading. Static symlink escapes are addressed in source, but race resistance and runtime behavior remain unverified, so Gate B stays open.

### Next decision and stop condition

**Paid canary: approved with prerequisites, not runnable yet.** The human
approved exactly one paired canary, one repetition, with a maximum spend of
`$500`, and subsequently selected OpenRouter MiniMax M3 as the comparison
route. The parent contract now binds the exact tuple `http://localhost:4000/v1`,
gateway alias `openrouter`, and provider model
`openrouter/minimax/minimax-m3`. The fail-closed child guard and receipt
validator require this tuple and the child hash to match the active parent.
This route decision does not itself start a provider request.

Remain stopped until a provider-enforced cap reference with explicit headroom
for delayed enforcement and authenticated retrieval of an authoritative
OpenRouter/MiniMax cost export are verified, and a schema-v3 child contract
binds the current parent hash, approved workload hash, route tuple, accounting
mode, one repetition, and maximum spend. The `$500` parent ceiling is not a
provider-enforced cap. Phase 442's metadata checks establish configured alias
mapping and credential acceptance only; they do not establish model inference,
provider cap enforcement, or cost-export availability. If only aggregate costs
are available, do not represent them as request-level cost or model evidence;
the child must meet the applicable isolation, complete-bucket, usage, and
headroom requirements in the Q4 contract. Stop if export coverage is
incomplete or the hard-limit reserve cannot be justified. Preserve the accepted
workload, prompt, oracle, and pinned client versions. Phase 436 rejects child
caps above the parent ceiling, and Phase 437 binds provider-reported costs to
the child. Phase 440's server-process persistence choice remains a separate
open decision.

**Gate E: continue only within the approved test boundary.** Phase 434 verifies
the loopback request handler with deterministic isolated callbacks,
concurrency, cancellation, timeout, circuit behavior, and cleanup. Phase 435
attempt 01 failed after 28 accepted requests with no captured fallback reason.
Attempt 02 failed after 27 accepted requests and captured two
`router_queue_timeout` responses. No child survived either run and resource
reserves remained safe. Attempt 02 used the old 5-second proposal and
12-second HTTP timeouts, not the approved 20/30-second retry settings. The
runner has since been corrected to those values and now requires `--run` to
start; help or a bare invocation cannot launch it. The human then gave fresh
Q4 approval for one corrected loopback fake-callback run. Attempt 03 passed
200/200 requests with zero failures and safe reserves. The approval is
consumed. No provider/model call, production route, or further soak is
authorized. The soak did not exercise the model worker or establish sustained
production-path operation. Phase 438 verifies only schema-bound router-state
helper recovery across object reconstruction. Gate E remains open for
model-worker restart and serving-process recovery, full accounting,
no-mutation behavior, and sustained operational shadow through the required
serving lifecycle. Phase 441 closes a malformed-result gap in the test-only
callback boundary, but does not add restart persistence or production-path
evidence. Phase 440's recommended opt-in server-state persistence change
requires a separate Q4 `human.choose_option` decision before editing the
server lifecycle; its advisor recommendation is not authorization. Keep
production routing disabled.

**Canary and utility gates.** Preserve and count auxiliary title requests in
all future comparisons. They are real model traffic and need per-request
client, purpose, and route attribution plus latency, token, cost, retry,
correction, abstention, and fallback accounting. A local stub or a single
paired case cannot establish teacher parity, Gate C confidence intervals, or
Gate D's weighted coverage and net-savings thresholds. When authorization
prerequisites are satisfied, evaluate the unchanged real workload and then the
matched three-arm replay. Stop on missing accounting, provider spend without a
valid contract, verifier failure, unexpected mutation, prohibited acceptance,
unbounded retry, or a breached resource reserve. Do not place credentials in
the repository, packet, or receipt.

Phase 452 adds tokenizer-ID totals for completed local Transformers generation
attempts, including bounded repair attempts, to the workflow accounting
receipt. When the native upstream path adds frontier calls after local
inference, the receipt now retains and reports both sources separately before
summing workflow tokens. Upstream attempts without usage, client-level
corrective HTTP retries, raised generation calls, durable replay-trace
serialization, complete workflow outcomes, dollar costs, and the matched Gate
D replay still require separate evidence before making a net-savings claim.
