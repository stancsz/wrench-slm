# E0 deterministic context runtime

Status: complete for the query-ranked assembly increment
Supervisor: root agent as goal owner
Started: 2026-09-23 (America/Edmonton)

## Product outcome

Advance Wrench from the completed v2 realignment into the first useful E0
runtime capability: bounded context assembly should use query-ranked exact
evidence while preserving explicit hot context and reporting what it considered
and omitted. This reduces manual context gathering for developers using coding
agents, while keeping evidence inspectable and the no-model baseline
deterministic.

The customer, value hypothesis, and long-term product evidence remain in the
[North Star](../../northstar/README.md) and [E0-E4 experiment](../../northstar/V2_EXPERIMENT.md).
This goal covers one production-directed E0 increment. It is not full E0, full
v2, or a production qualification claim.

## Acceptance

- Query and bounded lexical BM25 candidates affect context assembly.
- Explicitly preserved and hot context retain priority; matching reference and
  cold segments can be retrieved within the active token budget.
- Candidate IDs, search limit, selected evidence, and omission reasons are
  included in deterministic receipts.
- Ledger text and metadata admission, segment count, summary references, query
  length/terms, and term-document checks have hard
  limits applied before tokenization/traversal; the receipt reports when query
  work was truncated.
- Invalid limits, missing preserved segments, and mandatory evidence overflow
  fail closed.
- Focused context tests and `git diff --check` pass. No model, provider,
  training, or benchmark run is required for this deterministic slice.
- Changes are independently reviewed, documented, and committed without
  including unrelated workspace edits.

## Scope and constraints

Read [architecture](../../northstar/V2_ARCHITECTURE.md),
[experiment](../../northstar/V2_EXPERIMENT.md),
[storage/recovery](../../northstar/STORAGE_AND_RECOVERY.md), and the
[v2 realignment reuse audit](../../reports/wrench-v2-realignment/reuse-audit.md).
Keep all Wrench-owned footprint below 50 GB decimal. Any artifact-producing
job requires a fresh status and reservation. Preserve 10% RAM/VRAM free for
any workload that uses those resources. Do not download models, train, infer,
spend, publish, deploy, or enable production routing.

## Tasks and progress

| Task | Status | Evidence |
| --- | --- | --- |
| Connect bounded lexical retrieval to assembly | Complete | [context source](../../../src/wrench_harness/context.py), [focused tests](../../../tests/test_context.py) |
| Add independent critique and record observed checks | Complete | [E0 review](../../evals/wrench-e0-context-runtime/review.md) |
| Integrate, commit, and set next E0 action | Complete | This goal, [goal index](../README.md), and [review](../../evals/wrench-e0-context-runtime/review.md) |

## E0 work still outside this goal

The separate snapshot identity, artifact storage and roundtrip, namespace
registry, serialized prompt gate, structural index, outcome receipt, and
caller-owned preparation slices are now recorded in the goal index. Their
acceptance is component evidence, not full E0 milestone acceptance. Runtime
matched serialization, complete deterministic-baseline accounting, and
end-to-end authority checks remain E0 exit evidence. The POSIX-host snapshot
follow-up is complete; see the [snapshot retrieval goal](../wrench-e0-snapshot-retrieval/GOAL.md).
Matched-task utility and full request-lifecycle accounting remain E4 gates. The
larger product proceeds through E1-E4 only after experiment stage gates pass.

## First integration target: OpenCode V2

OpenCode V2 is selected as the first client integration target; its plugin
integration is not implemented. The bounded, uninstalled adapter contract is
recorded in [E0 OpenCode V2 context adapter contract](../wrench-e0-opencode-context-adapter/GOAL.md).
The documented context hook can edit assembled semantic system instructions
and messages immediately before a model request. OpenCode does not document a
dispatch-veto contract for this hook, and it does not establish provider
tokenizer or wire equivalence, or tool authority. See the official
[V2 plugin guide](https://opencode.ai/v2/docs/build/plugins) and
[V1 migration guide](https://opencode.ai/v2/docs/build/plugins/migrate-v1).

Strict E0 no-model preparation remains standalone. An adapter must bind the
correct session/worktree root to an exact source snapshot, gate the full
semantic request projection, and preserve the supplied tools map. Fixture
results support mechanics only. No consented matched-task corpus or outcome
oracle is designated, so they do not establish E4 utility.

## Next action

Next: implement and verify only after OpenCode version, provider serializer,
tokenizer, active-session root semantics, and dispatch authority have pinned
contracts. Until then, keep runtime identity, full accounting, authority, and
matched-task evidence open; do not claim a production route.
