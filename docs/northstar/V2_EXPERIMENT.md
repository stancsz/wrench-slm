# Experiment v2: useful Layer 1 decisions that improve from experience

Status: defined; bounded E0 components exist, end-to-end E0 acceptance and model trials have not started
Owner: human product owner
Planning date: 2026-09-23 (America/Edmonton)

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

Current inspection reports RTX 5060 Ti, 16,311 MiB total and 15,219 MiB free
VRAM, with about 17.85 GB RAM free of 34.29 GB. This is an instantaneous
inventory, not a benchmark or proof of target-device support. Recheck before
jobs. Preserve 10% free RAM/VRAM throughout.

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
