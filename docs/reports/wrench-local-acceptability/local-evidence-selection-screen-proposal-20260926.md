# Local evidence-selection screen proposal

Date: 2026-09-26
Status: proposed, awaiting separate inference authority; no fixture or model run

## Why this is the next local decision to measure

Wrench's Layer 1 controller is meant to choose relevant evidence before a
downstream model receives a request. That is a bounded decision that can
reduce downstream context, preserve the task for the larger model, and be
judged against an exact source-ID oracle. It is a more direct local-controller
question than another broad coding answer screen.

Current evidence accepts no semantic local SLM class. Prior local Qwen runs
failed their exact answer/tool-flow gates. The earlier 11.64% result is only a
synthetic prompt-input proxy. Actual matched frontier-token savings remain
N/A with zero eligible pairs.

## Proposed one-shot screen

Use one newly authored, isolated, Wrench-owned synthetic fixture, with 12
cases:

- Eight answerable evidence-selection cases: exact identifier versus
  near-match; a log line with its implementation; a two-file dependency;
  bounded literal search; misleading distractors; source freshness; required
  evidence within budget; and untrusted source text containing prompt-injection
  bait.
- Four abstention cases: missing required source, stale source, unresolved
  ambiguity/conflict, and absent or over-budget required evidence.

The model sees only the task query and candidate evidence, including random,
nonsemantic evidence IDs. Each ID is bound in the oracle to a snapshot hash,
path, source hash, and line range. It returns a strict selection or a strict
abstention. The oracle, labels, expected IDs, and case metadata stay out of
model-visible input. No tools or write actions are exposed.

Freeze the exact permissible ID set and abstention reason for each case before
invocation. A screen candidate must get all 8 positive selections exact and
all 4 abstentions exact, return valid schema for every case, select no stale,
unsupported, or out-of-snapshot ID, leak no fixture oracle, and cause no source
mutation. Any miss or boundary error rejects the class for this diagnostic.
One pass only; retire the fixture after invocation. A pass would justify a
larger held-out diagnostic, not real-work acceptance or production utility.

## Measurements and claim boundary

Record exact local controller input/output token IDs, per-case latency, and
RAM/VRAM minima separately. For each positive case, a fixed reference
tokenizer may compare complete candidate context with the exact selected
context:

`100 * (1 - selected_context_tokens / all_candidate_context_tokens)`

Report the arithmetic mean, ratio of sums, exact-selection count, and
abstention count separately. Until the OpenCode route's immutable model and
matching serializer/tokenizer are known, any downstream tokenizer result is
only a labeled reference-tokenizer proxy. The active localhost:4000 route is
not known to be local or immutable. This screen has no frontier request and
cannot produce a frontier-token savings percentage.

## Admission and authorization gates

- Separate explicit authority is required for local model inference under
  `COLLABORATION_CONTRACT.json`; approval to build this proposal is not that
  authority. A request for one bounded run is pending.
- Before the run, author and independently review the new fixture, protocol,
  runner, scoring oracle, one-shot exposure marker, output cap, and stop path.
  Do not reuse exposed fixtures or responses.
- Reconfirm the exact Qwen revision, every model and tokenizer file hash/byte
  size, runtime and serializer identities. Download, installation, training,
  provider/client traffic, network access, and retries are excluded.
- Run the storage status and a unique peak reservation, verify destination
  free space, and preserve at least 10% RAM and VRAM. Record admission before
  invocation. Stop on any inventory, hash, resource, or runner mismatch.

The full product question still requires authorized matched downstream tasks,
actual request/usage receipts, and independently verified successful outcomes.
The current average frontier-token saving remains **N/A**, not zero percent.

## Independent design review

Read-only subagent review recommended this 8-positive/4-boundary design and
confirmed that existing E0 receipts expose selected/omitted IDs but the prior
five-case screen tested only required-ID inclusion. Three review tracks found
that the current OpenCode adapter still stops before final request lowering,
and no exact downstream serializer/tokenizer is pinned. No reviewer loaded a
model/tokenizer, ran a screen, called a client/provider, or changed files.

See the [current acceptability map](local-work-acceptability-map-20260926.md),
[frontier readiness review](../../evals/wrench-local-acceptability/frontier-token-readiness.md),
and [pilot-readiness goal](../../goal/wrench-northstar-pilot-readiness/GOAL.md).
