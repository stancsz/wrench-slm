# Local acceptability bar critique

Date: 2026-09-25 (America/Edmonton)

- Goal: [Measure acceptable local work](../../goal/wrench-local-acceptability/GOAL.md)
- Job ID: `W2-LOCAL-ACCEPT-BAR-CRITIQUE-20260925`
- Nonce: `LABC-2B71`
- Repository revision inspected: `3c9cb277a311e705e225c9322fd3f0d6bdd3ff2f`
- Scope: static repository review only

## Decision

Keep training stopped. Current evidence supports bounded deterministic
operations on supplied synthetic snapshots and four exact, review-only patch
draft mechanics. It supports no semantic SLM work class, completed local
coding task, real-work utility, or frontier-token savings. The acceptance
envelope says this distinction directly and lists the narrow exact read,
line-read, literal-search, and draft forms ([acceptance envelope](local-acceptance-envelope-20260925.md#decision), lines 7-21).

The newest prompt-only result reinforces the SLM decision: the pinned model
had zero exact positive accepts among 12 answerable prompts, with three of six
boundary cases abstained correctly. Those were 3/18 complete case passes, not
three completed tasks ([screen report](prompt-only-local-work-screen-01.md#results),
lines 29-55). The exposed, tool-free screen cannot satisfy the goal's
held-out, tool-backed gate ([screen report](prompt-only-local-work-screen-01.md#decision),
lines 10-25). The goal records this result and keeps training stopped ([goal](../../goal/wrench-local-acceptability/GOAL.md), lines 10-14).

## Operational bar

| Route | Accept locally when | Abstain or escalate when |
| --- | --- | --- |
| Deterministic read/search | Request resolves to a unique, current source in the caller-supplied snapshot; operation and size are allowlisted and bounded; executor output exactly matches the frozen observation contract. | Missing, stale, ambiguous, out-of-range, oversized, or unsupported request; snapshot mismatch; tool/runtime error. Return the measured reason and ask for clarification or use a human/frontier route. |
| Deterministic patch draft | Only the four tested single-file UTF-8 LF operations, with unique literal/anchor, exact file list and target diff, independent verifier pass, `review_only=true`, `applied=false`, and unchanged source tree. | Any semantic intent, multiple files, non-unique target, format ambiguity, verifier mismatch, or request to apply. Keep it a proposal for human review. |
| SLM-generated task work | No class qualifies today. Future acceptance requires a preregistered fresh holdout, an independent task outcome oracle, evidence grounded in actual authorized tool results, correct completion or explicit abstention/escalation, and zero prohibited actions or mutations. Assess task success and safety separately from schema validity. | Any missing/contradictory evidence, unsupported answer, invalid output, failed oracle, or unmeasured class. Treat the output as untrusted and escalate. |
| Frontier-token savings | Report only from complete matched baseline and Wrench workflow receipts, for the same frozen task and downstream route, including retries, verification and fallback. Report per-task results, arithmetic mean, valid-pair count, and ratio-of-sums. | Missing counts, incomplete call accounting, mismatched route/tokenizer, or failed identity/outcome join makes the pair unknown/excluded, never zero. |

The deterministic thresholds follow the existing exact-outcome, boundary,
mutation, and verifier rules ([acceptance envelope](local-acceptance-envelope-20260925.md#acceptance-rule),
lines 25-37). Their demonstrated scope is mechanics on exposed fixtures, not a
general safety certification or end-to-end task success. In particular, the
176-case route screen executed no tools or verifier, while the smaller
route-to-executor screens used explicit synthetic snapshots ([work envelope](local-work-envelope-20260924-01.md#interpretation),
lines 14-25; [operation screen 02](local-exec-acceptability-02.md#result),
lines 5-26).

For SLM promotion, keep the current all-cases pass as a diagnostic stop rule,
not a statistical production bar. A future acceptance study needs independent
held-out tasks, a predeclared sample-size and quality margin, paired task
outcomes and confidence intervals. The v2 experiment already requires paired
final-task success and confidence intervals, zero prohibited accepts, and an
INCONCLUSIVE result when power is insufficient ([V2 experiment](../../northstar/V2_EXPERIMENT.md#accounting-and-quality-gates),
lines 93-109).

## Token savings are a separate result

Local prompt/model token counts and deterministic operation passes do not
measure paid downstream savings. The prompt-only run reports zero frontier
calls and zero matched pairs ([screen report](prompt-only-local-work-screen-01.md#runtime-and-accounting),
lines 73-81). The current readiness review likewise says there are no eligible
matched usage pairs and savings are N/A ([frontier readiness](../../evals/wrench-local-acceptability/frontier-token-readiness.md#decision),
lines 7-10). The v2 formula requires complete matched call accounting and a
nonzero baseline denominator ([V2 experiment](../../northstar/V2_EXPERIMENT.md#accounting-and-quality-gates),
lines 119-123). Quality failures remain in token totals; savings cannot be
called useful if task success falls.

## Recommended next measurement

Do not train. Run one preregistered, offline, tool-backed diagnostic with the
current pinned base model and a fresh Wrench-authored synthetic fixture. Pick
one bounded task class where the deterministic read/search path supplies
source evidence, such as exact function localization. Freeze positive cases,
missing/stale/ambiguous and misleading near-match boundaries, exact output
schema, and an independent source-derived outcome oracle before the run. Keep
the fixture out of training and tuning.

Primary metric: **verified local task completion rate**, the number of cases
whose final answer matches the independent outcome oracle and cites required
evidence from actual tool results, divided by all eligible cases. Show the
denominator and break out correct accepts, correct abstentions/escalations,
false abstentions, wrong accepts, unresolved cases, latency, and prohibited
actions. Compare paired cases with the deterministic-only route so the study
shows whether generation adds task value beyond exact retrieval. Any wrong
accept or prohibited action fails the safety gate; insufficient sample power
is INCONCLUSIVE. This measures a local task hypothesis without training, but
remains synthetic mechanics evidence, not real-work acceptance.

Do not attach a token-savings percentage to this offline run. To measure that,
first obtain the separately required participant/source consent and provider
authority, then preregister matched downstream arms and complete usage
accounting. The readiness review records that these authority and route
identity gates are not met today ([frontier readiness](../../evals/wrench-local-acceptability/frontier-token-readiness.md#data-identity-and-authority-gates),
lines 43-62, 68-80).

## Limitations

This is a static critique of Wrench-authored synthetic evidence. It does not
validate receipts independently, establish representativeness, approve
provider use, or demonstrate a production-level acceptability threshold. The
repository had an unrelated modified E0 pipeline and pre-existing untracked
owner files during inspection; this report is the only file changed for this
job.
