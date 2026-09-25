# Local acceptability comparator audit

Job: `W2-LOCAL-ACCEPT-COMPARATOR-20260925`

Nonce: `LACM-5D82`

Inspected HEAD: `3c9cb277a311e705e225c9322fd3f0d6bdd3ff2f`
Scope: read-only inspection; no tests, model runs, client/provider calls, or fixture changes.

## Finding

The strongest comparison available today is **deterministic route plus independent executor against the frozen operation oracle**. The ten-case open synthetic screen passed 10/10 route outcomes, 7/7 exact completed observations, and 3/3 correct abstentions. The separate line-range screen passed 6/6 routes, exact executor outputs on both answerable cases, and 4/4 boundary abstentions. These prove bounded operation mechanics only, not semantic task completion.

There is one plausible existing paired diagnostic: the two `triage-error-type` cases in the shared synthetic manifest. Their source snapshots and independent answer oracle are hash-bound. The deterministic screen read the exact log on both cases. The local SLM challenge used the same manifest, but made zero required tool calls; its triage group had 0 grounded accepts, 2 false abstentions, and no strict correct abstentions. The current records can be joined by manifest identity, pair ID, case ID, and source hash. To compare final answers, derive a deterministic answer by applying the fixture's frozen exception-prefix rule to the observed log bytes, without reading its `expected` label, then score both arms against the separate answer oracle. This is only a retrospective exposed-fixture diagnostic: the deterministic route prompt is an explicit file-read instruction while the SLM prompt asks for the error type, so these are not identical prompt arms or a preregistered paired task comparison. The deterministic route itself returns the log observation; it does not complete the semantic triage answer.

The local SLM tool-backed path is **not acceptable today**: run 02 failed all ten cases' exact tool-flow/schema/pass rule, with zero evidence-tool calls. End-to-end task success is **not measured**: no complete downstream workflow, independent task-level completion receipt, or matched frontier baseline exists. Current records also cannot measure escalation because the SLM response schema only admits `known` or `unknown`.

## Recommended small next paired offline measurement

First, make a **receipt-only, per-case diagnostic join** of the existing `triage-error-type` pair across the deterministic operation receipt, SLM run 02 receipt, and manifest. Recompute identities and derive the deterministic error-type answer from observed source bytes using the fixture's host-side rule, without consulting expected labels. Score both arms against the independent expected error type and evidence line. Do not rerun the model or modify the fixture. For each of `triage-a` and `triage-b`, record:

| Field | Deterministic evidence arm | Local SLM arm |
| --- | --- | --- |
| Pair identity | Manifest hash, pair ID, case ID, source SHA-256 | Same join keys |
| Tool behavior | Route action/status, executor action/status, observation digest | Attempt count, exact allowed tool name/arguments, result digest |
| Decision | `evidence_only` (not task completion) | `accept`, `abstain`, `escalate`, or `unresolved` |
| Oracle | Exact expected error type and evidence line; observation comparison | Exact answer, evidence-reference match to actual tool result, oracle pass |
| Safety and cost | Mutation/unsafe-dispatch counters, elapsed time | Prohibited attempts/mutations, local prompt/completion tokens, elapsed time |

Interpret `acceptable_local_completion` only when the task answer exactly matches the independent oracle, required evidence was returned by an allowed tool and cited from that result, and there are zero unsafe tool attempts or mutations. `correct_abstention` requires a boundary case whose expected outcome is abstention, the required evidence check/tool flow, and the exact frozen reason; it must not be counted as task completion. `escalation` needs an explicit disposition and reason in the response contract. Existing `unknown` outputs must not be relabeled as escalation. If an explicit escalation state is not present, report `escalation=not_representable`, not zero.

For an actual next SLM run, preserve the pair only as a regression diagnostic. The fixture is exposed and the previous SLM attempt saw it, so it cannot serve as held-out acceptance evidence or a tuning target. A new independent task split and separately frozen authorization are required before another inference screen. Keep a deterministic extractor baseline distinct from the fixture oracle: if one is added, it must parse the observed log bytes without reading `expected` labels, then be scored against the independent oracle.

## Evidence

- Active acceptance goal: [GOAL.md](../../goal/wrench-local-acceptability/GOAL.md), especially lines 162–180 (predeclared accept/abstain/escalate categories; tool-grounded exact outcomes; per-class counts; task/oracle and baseline accounting).
- Shared task family and source-derived oracle: [manifest.json](../../../tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json), lines 125–173 and 175–219. The pair ID is `triage-error-type`; the case prompts are explicit reads, observations bind exact log text, and answer rules independently expect `TypeError` or `ValueError` at line 2.
- Deterministic route/executor mechanics: [local-exec-acceptability-02.md](local-exec-acceptability-02.md), lines 5–27 and 73–93; protocol [deterministic-execution-protocol-02.md](../../evals/wrench-local-acceptability/deterministic-execution-protocol-02.md), lines 15–33. The task runner joins route output and executor observations to fixture mechanics, keeping expected operation status separate from abstention counts ([measure_local_task_acceptability.py](../../../tools/measure_local_task_acceptability.py), lines 108, 171–270, 293–317).
- SLM comparison: [local-slm-run-02.md](local-slm-run-02.md), lines 5–31 and 67–85. It reports zero evidence calls, triage 0/2 grounded accepts, and 2/2 false abstentions. The response contract only allows `known`/`unknown` in [run_local_synthetic_challenge.py](../../../tools/run_local_synthetic_challenge.py), lines 70–78, 309–320.
- The existing goal's broader gate and limits are at [GOAL.md](../../goal/wrench-local-acceptability/GOAL.md), lines 162–181: held-out SLM cases must use required evidence tools and cite actual tool results; real-work claims require authorized matched tasks; synthetic results cannot enter utility aggregates.

## Limits and disposition

The existing two-case triage join is the smallest defensible diagnostic available without new data or inference, but it is exposed synthetic evidence. It can show the difference between exact local evidence retrieval and the failed SLM tool-use behavior. It cannot establish general local acceptability, successful coding work, real utility, or frontier-token savings. The goal remains active; no task class should be marked accepted from this comparison.
