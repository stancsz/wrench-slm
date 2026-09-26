# Local work acceptability map (2026-09-26)

## Decision

Closed 2026-09-26 by owner decision: the small local SLM as an OpenCode
primary agent or semantic controller is not feasible for the intended
workflow. Existing Qwen 0.8B semantic screens failed their acceptance gates.
No real-work class passed an end-to-end outcome check. Training remains
stopped. See the [direction closure report](direction-closure-20260926.md)
and [evaluation](../../evals/wrench-local-acceptability/direction-closure-20260926.md).

This is a scoped product decision, not proof that all 2B models fail. No 2B
model was tested. Full-lifecycle frontier savings and the deterministic
context-preparation hypothesis remain unmeasured.

The fresh failing-test evidence-packet screen stopped before scoring because
of a runner/oracle comparison defect; it adds no accepted scope. Its exposed
fixture is quarantined from reruns.

## Measured envelope

An evidence-selection protocol, fixture, test, and runner were prepared after
the owner decision. They were not run and are outside the closed result.
Separate inference authority remains pending. See the
[protocol](../../evals/wrench-local-acceptability/local-evidence-selection-screen-01-protocol.md).

The newest five-case E0 context integration attempt recorded the expected
synthetic mechanics branches, but is inadmissible because the required separate
orchestrator admission record is missing. It adds no accepted scope. The
fixture is exposed and quarantined; details are in the [diagnostic report](local-context-integration-screen-01.md)
and [evaluation](../../evals/wrench-local-acceptability/local-context-integration-screen-01-result.md).

| Work type | Observed result | What the result supports |
| --- | --- | --- |
| Deterministic failing-test evidence packet, screen 01 | Aborted on the first positive packet comparison; 0/3 positive cases completed, 0/3 boundaries reached; no score | Runner defect only. The fresh fixture is exposed; no task acceptance or rejection follows. See the [failure evaluation](../../evals/wrench-local-acceptability/failing-test-evidence-packet-screen-01.md). |
| E0 localization screen 02, tokenizer-only | Attempt stopped at runtime-lock identity check before tokenizer load or case execution; 0/4 positives and 0/4 boundaries scored; no receipt | No token-reduction or acceptability result. The fixture is exposed; do not rerun. See the [attempt report](localization-screen-02.md) and [protocol](../../evals/wrench-local-acceptability/localization-screen-02-protocol.md). |
| Local SLM read-only configuration fact retrieval, screen 01 | 0/12 exact grounded positives; 0/8 correct boundary abstentions; 20/20 invalid outputs; 0 prohibited actions | This task class is not accepted for the local SLM at the measured model/runtime identity. |
| Deterministic exact line-range reads and fail-closed boundaries | 6/6 routes matched; 2/2 executor reads exact; 4/4 boundary abstentions correct | Synthetic operation mechanics only; no model or task completion. |
| Deterministic single-operation review-only patch drafts | 12/12 proposed diffs matched frozen targets under an in-memory check; 9/9 boundary abstentions | Replacement, append, insert-after-unique-line, and explicit whole-line removal on small UTF-8/LF fixtures. No patch was applied to a repository, and no semantic fix quality was measured. |
| Evidence selection for log triage, exhaustive literal search, exact config reads | 5/7 positive cases met evidence gates; 4/4 abstention boundaries passed | Synthetic E0 context-selection behavior. Complete M3 input-token IDs fell 11.64% on average (3,204 baseline to 2,816 selected-context tokens, 12.11% ratio-of-sums). No generated answer or local SLM call. |
| Local SLM semantic work: localization, triage, context selection, evidence-grounded answers | Prior tool-backed Qwen screen: 0/10 cases; 5 false abstentions and 2 unsupported known claims. Prompt-only screen: 0/12 positive accepts, 3/18 total passes. | No semantic task class is accepted for the local SLM. These are exposed synthetic diagnostics, not customer-work estimates. |
| Local SLM configuration edit review | Latest run: 0/2 attempted cases passed, then stopped; 10/12 not run | The first answer proposed no change and skipped its evidence read; the next answer was invalid JSON. This workflow currently fails its local gate. |
| Frontier-token savings | 0 actual matched exact-usage pairs; 0 pairs with independently verified completion in both arms | **N/A**, not 0%. The reporter separates all-usage diagnostics from the success-qualified mean. No provider calls or matched downstream usage receipts exist. |

The 11.64% figure above remains a synthetic prompt-input proxy from an earlier
tokenizer-only screen; it is not end-to-end savings. No practical frontier
token-saving rate is measurable yet.

## Interpretation

The positive deterministic results say the bounded router/executor can follow
frozen mechanics. They do not show that a local model can choose the right
operation, produce a useful semantic answer, or complete a coding task. The
11.64% context-selection figure is a tokenizer-only synthetic input reduction;
it is not end-to-end token savings and does not include generated output,
verification, retries, repairs, or fallback.

The fresh read-only configuration fact screen also failed its gate: all 12
positive outputs were invalid, and all eight boundary outputs were invalid.
There were no prohibited actions, but the SLM made no exact grounded completion
and no correctly shaped safe abstention. This rejects configuration fact
retrieval as an accepted local SLM task class at the measured model/runtime
identity. Do not train on this exposed screen or tune against its answers.

The [screen 01 result](../../evals/wrench-local-acceptability/read-only-config-fact-screen-01-result.md)
records the frozen 20-case failure and local token/latency cost. Any future
semantic screen needs a new, independently authored fixture and protocol; this
fixture must not be rerun or used for tuning. For the North Star total-token
percentage, the production-directed next measurement is a full-lifecycle
matched-task ledger that joins the actual downstream request, every retry and
fallback, local processing tokens, and verified task outcome. The reporter's
success-qualified mean now requires independently verified completion in
both arms; it does not authenticate those caller-supplied claims. E0 still
lacks the actual client dispatch/usage join. An offline mixed-lifecycle
receipt adapter now represents local and frontier attempts, retries, tools,
verification, and fallback, but downgrades caller-supplied verification
claims. A static-review finding where a `not_run` work-call row with a local
or frontier route counted as executed is fixed: those rows now reject, while
`none/not_run` remains a non-call. Its focused synthetic suite passes 7/7.
The adapter still does not produce a success-qualified pair or actual savings
measurement.
See the [adapter report](mixed-lifecycle-ledger-bridge-20260926.md) and
[evaluation](../../evals/wrench-local-acceptability/mixed-lifecycle-ledger-bridge-20260926.md),
plus the [OpenCode offline request-boundary report](../wrench-e0-opencode-context-adapter/offline-request-boundary.md).

## Evidence

- [Read-lines operation screen 03](../../evals/wrench-local-acceptability/read-lines-operation-screen-03.md) and [its review report](local-read-lines-acceptability-03.md)
- [Patch operations screen 01 result](../../evals/wrench-local-acceptability/patch-operations-screen-01-result.md)
- [Synthetic context token reduction screen 01](../../evals/wrench-local-acceptability/synthetic-context-token-reduction-screen-01.md) and [protocol 06](../../evals/wrench-local-acceptability/synthetic-context-token-reduction-protocol-06.md)
- [Tool-backed Qwen run 02](local-slm-run-02.md) and [prompt-only local-work screen](../../evals/wrench-local-acceptability/prompt-only-local-work-screen-01-result.md)
- [Configuration draft screen 01 result](../../evals/wrench-local-acceptability/local-config-review-draft-screen-01-result.md)
- [Read-only configuration fact screen 01 result](../../evals/wrench-local-acceptability/read-only-config-fact-screen-01-result.md) and [protocol](../../evals/wrench-local-acceptability/read-only-config-fact-screen-01-protocol.md)
- [Success-qualified frontier savings metric report](success-qualified-frontier-savings-metric-20260926.md) and [evaluation](../../evals/wrench-local-acceptability/success-qualified-frontier-savings-metric-20260926.md)
- [Mixed-lifecycle ledger bridge report](mixed-lifecycle-ledger-bridge-20260926.md) and [evaluation](../../evals/wrench-local-acceptability/mixed-lifecycle-ledger-bridge-20260926.md)
- [Frontier-token readiness gate](../../evals/wrench-local-acceptability/frontier-token-readiness.md)

All reported screens use development/synthetic material. None establishes
held-out generalization, production utility, or real-task acceptability.
