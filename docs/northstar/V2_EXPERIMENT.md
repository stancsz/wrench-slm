# Experiment v2: useful Layer 1 decisions that improve from experience

Status: staged; E0 is not accepted. The owner stopped the tested small local
semantic-controller direction on 2026-09-26. Full v2 acceptance and end-to-end
frontier-token savings remain unmeasured.
Owner: human product owner
Planning date: 2026-09-23 (America/Edmonton)

## Owner decision, 2026-09-27: bounded gateway experiment reopened

The owner requested a fresh experiment for a small Wrench LoRA gateway plus a
stronger coding model, targeting at least 95% of strong-model-only completed
task value at no more than 5% of its all-in cost, while supporting sustained
engineering. This supersedes the 2026-09-26 pause only for the narrow,
staged gateway experiment described in the
[gateway goal](../goal/wrench-gateway-model-research/GOAL.md). It does not
reopen the 0.8B model as a general OpenCode agent, change E0-E4 acceptance, or
make a production claim.

For an initial local diagnostic, the owner authorizes new Wrench-authored
synthetic train/dev/held-out data and one bounded LoRA candidate experiment on
the already-present Qwen3.5-0.8B snapshot, conditional on the storage, hash,
compatibility, 10% RAM/VRAM and exact reservation gates. The LoRA may propose
finite source-linked context and routing decisions only. Deterministic code
retains all authority and execution.

The owner specified `http://127.0.0.1:4000` for the stronger route. On
2026-09-27 the read-only live route snapshot was `active_model=openrouter`,
`mode=force`, `policy_version=4`; the previously audited mapping points to
OpenRouter/MiniMax M3. The dollar cap is still unspecified. Do not send
generation requests or alter route configuration until a cap, actual provider
identity, and usage accounting are frozen. At this initial decision, no new
model download, private or real task capture/transfer, adapter activation,
publication or production routing was authorized. The later candidate-scope
decision below expands model selection under the ordinary inventory and job
gates; it does not change the other exclusions.

See the [2026-09-27 readiness record](../evals/wrench-gateway-model-research/iteration-000-readiness-20260927.md)
and [LoRA screen protocol](../evals/wrench-gateway-model-research/lora-screen-01-protocol-20260927.md).

## Owner decision, 2026-09-27: candidate scope below 10B

The owner broadened model selection from the already-present Qwen3.5-0.8B to
any pinned model below 10B parameters that runs smoothly on this machine. This
supersedes the 0.8B-only candidate restriction above; it does not waive the
model-tree inventory, revision pin, storage reservation, exact runtime and
LoRA compatibility review, current hardware admission, or 10% RAM/VRAM floor.
The first model remains a comparison point, not a required winner. Model
selection and any candidate-specific download or run must follow the
[storage/recovery policy](STORAGE_AND_RECOVERY.md) and a separately bounded
job; this scope does not authorize paid calls, real-data capture, held-out
access outside the protocol, adapter activation, or production routing.

The owner also reconfirmed SubRoute at `http://127.0.0.1:4000`. A new
read-only check returned HTTP 200 from `/health/liveliness` and listed 19
aliases at `/models`; the `openrouter` alias metadata identifies the
configured MiniMax M3 target and $0.30/M input, $1.20/M output rates. The
individual upstream provider remains unverified without a generation receipt.
No generation request was made. The numeric aggregate spend cap is still
unspecified, and the local caller still needs a hard cap plus fail-closed
usage and billing receipts before a paid comparison.
See [iteration 010](../evals/wrench-gateway-model-research/iteration-010-model-scope-route-controls-20260927.md)
for the live read-only route fields, current resource sample, and candidate
research.

## Owner decision, 2026-09-28: select by smooth host fit and push a demo MVP

The owner removed the prior 2B preference. Any pinned, licensed model below
10B may be selected when the exact inference and LoRA-training packages fit
this host and run without OOM, lost work, or crossing the 10% RAM/VRAM reserve.
Record cold/warm latency, throughput, context, errors and peak resources. A
short smoke run proves only feasibility; representative coding tasks choose
the candidate, and an all-day workload is still required for sustained-use
claims. The already installed Qwen3.5-0.8B Q8_0 and Qwen3.5-4B Q4_K_M tags are
candidate packages, not smooth-run evidence. A first 4B Docker Ollama smoke
ran CPU-only, returned no answer after approximately four minutes, and brought
free RAM to 11.24%; it was stopped before the 10% reserve was crossed. A
separate container requested `--gpus all` but had no NVIDIA device node, so no
GPU inference ran. This rejects the current Docker paths, not the model under
a host CUDA runtime. See [Iteration
105](../evals/wrench-gateway-model-research/iteration-105-qwen35-4b-local-hardware-smoke-20260928.md).
The current 0.8B Fit-03 package
must be reviewed against the updated gateway-goal hash before a fit; 4B needs
its own exact training compatibility and peak-memory admission.

Push a provider-free demo MVP with Wrench context preparation, a real local
model, a deterministic code-task verifier, and paired baseline/prepared prompt
and all-token, latency, resource, retry and recovery receipts. The MVP may use
a fixed mock response to illustrate the frontier branch, explicitly marked
as mock. This does not alter the 95/5/95 and 95%-cheaper acceptance criteria,
authorize paid calls to forced SubRoute, or count a synthetic task as product
utility. See the [active gateway goal](../goal/wrench-gateway-model-research/GOAL.md)
for MVP definition and progress.

## Owner decision, 2026-09-26

The owner concluded that a small local SLM as the primary OpenCode agent or
semantic controller is not feasible for the intended Wrench workflow. The
tested Qwen 0.8B route failed repeated synthetic semantic acceptance screens,
including evidence/tool-use and output-contract requirements. The pasted
discussion about 2B models is rationale for the product decision, not Wrench
measurement; no 2B model was tested, so this is not a universal claim about
every 2B model or workflow.

The local semantic-controller investigation is closed. Do not continue model
screening, tuning, or training under this direction. The deterministic
context-preparation hypothesis is separate and remains unproven: its 11.64%
synthetic input-token reduction does not measure full-lifecycle frontier
savings. No eligible matched frontier-usage pairs exist, so actual savings
remain N/A. This decision does not mark E0-E4 or the complete v2 experiment as
accepted.

## Question and intended product

Can a deterministic context runtime plus a native small controller reduce the
paid work of a coding agent, while a small personal LoRA improves local
decisions without harming core behavior, safety or recoverability?

The intended end state includes the full Layer 1 pipeline and all three weight
components. A deterministic baseline, binary classifier, adapter file or
synthetic test pass cannot by itself complete this experiment.

Start with developers using OpenCode, DeepSeek Harness or Claude Code.
Use one supported integration for the first replay, then demonstrate the same
bounded context contract through all three before claiming full client support.
Do not add unrelated client integrations.

## Hypotheses and comparisons

| Hypothesis | Matched comparison | What could falsify it |
| --- | --- | --- |
| Context preparation removes paid mechanical work | Direct downstream baseline versus deterministic runtime | Extra retrieval/corrections erase token or latency savings |
| A small controller improves context choices | Deterministic runtime versus frozen Qwen plus Wrench-Core | No held-out quality/efficiency gain after inference overhead |
| Local experience improves behavior | Base+core versus base+core+personal on later tasks | No independent improvement, forgetting, unsafe routes or excessive training cost |
| The learning stack remains recoverable | Active/prior/candidate across interruption and reset | Corrupt activation, mutated base/core, missing sources or failed rollback |

The primary reference is [Headroom](REFERENCES.md), with Aider for repository
navigation. Compare actual supported workflows, not published percentages.

## Stages and exit evidence

| Stage | Work | Required evidence to proceed |
| --- | --- | --- |
| E0 deterministic baseline | Snapshot/index input, lexical and structural candidates, exact hot evidence, bounded context compiler, reversible artifact store, namespace registry, rule/no-model route and outcome receipts | Exact-source round trips, final serialized prompt within budget, explicit omissions/stale misses, zero unauthorized actions, complete baseline accounting |
| E1 core adapter | Verify pinned Qwen runtime/total size and adapter composition; train curated Wrench-Core decision tasks | Fresh group/repository holdout; improvement versus E0 on a predeclared decision metric after local overhead; no authority/regression failures |
| E2 experience and personal adapter | Opt-in local capture, reviewed labels, bounded replay, asynchronous candidate fitting with base/core frozen | Fresh temporal holdout; better personal-task decisions than base+core; no core gate failures, frozen base/core hashes and bounded resource cost |
| E3 promotion/recovery | Atomic active manifest, request version pinning, retained prior/factory state, delete/reset and core-version compatibility | Failed/incomplete candidates never activate; missing/corrupt files fail closed; restart, interruption and rollback restore expected outputs |
| E4 integrated utility | Matched replays across the three named clients, real tasks, cold/warm caches, concurrency, cancellation/timeouts and sustained use | All authority, quality, accounting, resource and operational gates; human production decision follows evidence |

Use the [E4 preregistration template](E4_PREREGISTRATION_TEMPLATE.md) to
freeze any future matched-task study. The template is protocol-only: completing
it does not admit data or authorize capture, transfer, or a run. The authored
synthetic seed remains mechanics-only and is excluded from utility aggregates.

This realignment prepares these stages. It does not run them. The initial
architecture builds E0 before fitting and replaces heuristics one decision
at a time: rerank, retrieve/stop, tool selection, routing, then compression
only where justified. Retain ablations so a slow or harmful learned component
can be disabled without dismantling the runtime.

The first bounded pilot should cover localization, failing-test/log triage and
tool/context selection across more than one repository/language. Include exact
identifiers, misleading near-matches, changed files, stale handles, missing
evidence, large required hot regions and prompt-injection attempts. Author
fixtures separately from real consented workflow traces; label their origin.

Before each experiment, freeze a small run manifest: task/repository groups,
source hashes, sample-size/power rationale, prompts, provider/local routes,
tokenizers, budgets, retry limits, success oracle, safety checks, primary
metric, promotion margin and stopping rules. Missing predeclaration is
INCONCLUSIVE, not an opportunity to choose a favorable metric afterward.

## Data and learning design

Replace the old fixed 25k binary-only allocation with evidence-driven decision
data. Do not reinterpret old six-action rows as context-selection labels.
The source six-action oracles remain reusable authority checks.

Each experience record needs request/session/task identity, snapshot and
candidate IDs, selected/omitted evidence, permitted choices, actual route,
outcome/verifier evidence, corrections, rights/consent, redaction/review,
base/core/personal identities and timestamps. Record ambiguity and discard
unverifiable learning targets. Never retain hidden teacher reasoning.

Split by repository/task family and time before training. Maintain separate
curated core training, development, immutable core regression, personalization
train/replay and fresh temporal holdout. Do not mine errors from the sealed
final set into training; retire an exposed evaluation set honestly and replace
it through a separately frozen process. Previously uncertain v1 final material
stays quarantined.

Corrections and failed-then-successful routes have high candidate value, but
are not automatically causal ground truth. Review and verify them. The notes'
replay percentages, ranks, batch cadence and example weights are tunable
hypotheses, not accepted production constants.

## Accounting and quality gates

Use these arms on identical frozen tasks and comparable downstream budgets:

1. Downstream stronger model only, with its normal context.
2. Deterministic Wrench plus the same downstream/fallback model.
3. Deterministic Wrench plus base+Wrench-Core controller and the same fallback.
4. The same system plus a personal adapter trained only on prior permitted data.

Count the full request lifecycle, including tool schemas, auxiliary/title
calls, verification, local inference, context rebuilds, cache misses, retrieval
page faults, repairs, retries and fallback. Report local token/compute/energy
and amortized learning costs separately from paid frontier tokens and dollars.

Report paired final-task success and 95% confidence intervals; zero prohibited
accepts, unexpected mutations, policy bypasses or data leakage is mandatory.
A component must improve its predeclared primary metric without material final
success regression. Insufficient power or uncertain non-inferiority is
INCONCLUSIVE. Do not turn a small diagnostic sample into a release claim.

Production ambitions retained from v1 are at least 95% net frontier-token
savings, at least 90% weighted mechanical-workload coverage and at least 50%
median/p95 end-to-end latency improvement on successful eligible tasks.
Keep the [legacy gates](../misc/v1/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md)
as the historical comparison contract. Predeclare a v2 release contract for
the broader workload before claiming production acceptance; the target cannot
be lowered after results merely to obtain a pass.

For observed frontier token savings use:
`1 - (all Wrench-workflow frontier tokens / all baseline frontier tokens)`.
Require a nonzero baseline denominator, matched tokenizer/usage conventions
and complete call accounting. "Net" also requires accounting for local
inference/verification/retries/training economics using an explicit frozen
cost conversion, not subtracting unlike tokens without explanation.

Frontier Token Share uses paid frontier tokens divided by a frozen reference
tokenization of the unique logical source material for the task. Report both
counts; do not add repeated local reads to the denominator. This metric cannot
substitute for baseline savings, task success or dollars.

For the personal adapter, require zero new core invariant failures, no material
paired regression, statistically supported improvement on the chosen fresh
personal metric, and save/load/reset parity. No threshold may be tuned on final
results. Sample size and acceptable quality margin must be set before a run;
the owner's illustrative 1-2% suggestion is not an automatic permission to
accept observed loss.

## Data source decision

Use the ranked [data-source plan](DATA_SOURCES.md) as a proposal, not data
admission. Today, use authored synthetic fixtures only. A future local-teacher
proposal run requires approved source snapshots and permitted use; pin its
actual identity and keep generated labels provisional until scripted checks
and independent human review. A future matched-task pilot requires participant
and per-task opt-in plus approved capture, storage, retention, withdrawal, and
deletion terms. Keep public benchmark splits evaluation-only unless provenance
is deliberately cleared.

## Host, storage and authority

The 2026-09-23 inspection reported RTX 5060 Ti, 16,311 MiB total and
15,219 MiB free VRAM, with about 17.85 GB RAM free of 34.29 GB. A fresh
2026-09-27 observation for the gateway study found 5,083 MiB free VRAM and
13.97 GiB free of 31.94 GiB RAM. These are timestamped snapshots, not proof
that a training or serving target fits. Recheck before jobs and preserve 10%
free RAM/VRAM throughout; use the current [readiness record](../evals/wrench-gateway-model-research/iteration-000-readiness-20260927.md)
for gateway-specific admission.

The [candidate manifest](model-candidate.json) pins a complete approximately
1.77 GB foundation snapshot. Adapters, optimizer state, tokenizers, runtimes,
index data, replay, backups and temporary copies all count toward the strict
50 GB aggregate ceiling. [Storage/recovery](STORAGE_AND_RECOVERY.md) is mandatory.
Bound rank/modules, batches, epochs, retention and output bytes before fitting.

Repository cleanup, design, metadata research and bounded offline verification
are authorized by this task. The next implementation milestone can proceed
within those reversible bounds. This document does not dispatch a training,
download, spend, publish or production-routing job. Job-specific admission,
approved data, tested recovery and applicable user authority remain necessary.
Historical USD 100 corpus and USD 500 canary approvals apply to their former
scope and do not authorize v2 spending.

Stop on missing data identity, unresolved label/consent access, authority
violations, active-version corruption, resource breaches or growth that cannot
be bounded. Preserve evidence and repair the issue before repeating a run.
If E1/E2 cannot beat their baselines after overhead, record that failure and
reconsider that learned component. Do not expand model size or revive pruning
to hide a failed hypothesis.

## Production path and open assumptions

Unverified work includes actual Qwen backend/dual-adapter behavior, useful
held-out decisions, outcome labels, data recovery storage, learning cost,
forgetting resistance, three-client integration, reliable cancellation and
sustained operation. The smaller-device and phone milestones follow a useful
validated desktop workflow. Multi-adapter banks and shared compute remain
later research.

A complete v2 result requires E0 through E4, with personal adaptation and
recovery demonstrated. The documentation/cleanup goal has its own narrower
completion audit and must never be presented as a completed v2 runtime.
