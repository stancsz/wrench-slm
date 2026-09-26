# Local work acceptability map (2026-09-26)

## Decision

Current evidence supports **bounded deterministic mechanics on synthetic
fixtures**, not semantic work completed by the local SLM. No real-work class
has passed an end-to-end outcome check. Keep training paused until one narrow
semantic class passes a fresh, independently scored local screen.

## Measured envelope

| Work type | Observed result | What the result supports |
| --- | --- | --- |
| Deterministic exact line-range reads and fail-closed boundaries | 6/6 routes matched; 2/2 executor reads exact; 4/4 boundary abstentions correct | Synthetic operation mechanics only; no model or task completion. |
| Deterministic single-operation review-only patch drafts | 12/12 proposed diffs matched frozen targets under an in-memory check; 9/9 boundary abstentions | Replacement, append, insert-after-unique-line, and explicit whole-line removal on small UTF-8/LF fixtures. No patch was applied to a repository, and no semantic fix quality was measured. |
| Evidence selection for log triage, exhaustive literal search, exact config reads | 5/7 positive cases met evidence gates; 4/4 abstention boundaries passed | Synthetic E0 context-selection behavior. Complete M3 input-token IDs fell 11.64% on average (3,204 baseline to 2,816 selected-context tokens, 12.11% ratio-of-sums). No generated answer or local SLM call. |
| Local SLM semantic work: localization, triage, context selection, evidence-grounded answers | Prior tool-backed Qwen screen: 0/10 cases; 5 false abstentions and 2 unsupported known claims. Prompt-only screen: 0/12 positive accepts, 3/18 total passes. | No semantic task class is accepted for the local SLM. These are exposed synthetic diagnostics, not customer-work estimates. |
| Local SLM configuration edit review | Latest run: 0/2 attempted cases passed, then stopped; 10/12 not run | The first answer proposed no change and skipped its evidence read; the next answer was invalid JSON. This workflow currently fails its local gate. |
| Frontier-token savings | 0 eligible matched pairs | **N/A**, not 0%. No provider calls or matched downstream usage receipts exist. |

## Interpretation

The positive deterministic results say the bounded router/executor can follow
frozen mechanics. They do not show that a local model can choose the right
operation, produce a useful semantic answer, or complete a coding task. The
11.64% context-selection figure is a tokenizer-only synthetic input reduction;
it is not end-to-end token savings and does not include generated output,
verification, retries, repairs, or fallback.

The local SLM evidence currently fails before a useful work class can be
approved. Prior runs show missing tool use, false abstentions, unsupported
claims, and invalid output. The most informative next gate is response-format
reliability and read-before-answer grounding for one narrow class, with a fresh
independently reviewed fixture, positive cases, boundary cases, and a frozen
outcome oracle. Count safe abstentions separately from completed tasks. Do not
train on the exposed screens or tune against their answers.

## Evidence

- [Read-lines operation screen 03](../../evals/wrench-local-acceptability/read-lines-operation-screen-03.md) and [its review report](local-read-lines-acceptability-03.md)
- [Patch operations screen 01 result](../../evals/wrench-local-acceptability/patch-operations-screen-01-result.md)
- [Synthetic context token reduction screen 01](../../evals/wrench-local-acceptability/synthetic-context-token-reduction-screen-01.md) and [protocol 06](../../evals/wrench-local-acceptability/synthetic-context-token-reduction-protocol-06.md)
- [Tool-backed Qwen run 02](local-slm-run-02.md) and [prompt-only local-work screen](../../evals/wrench-local-acceptability/prompt-only-local-work-screen-01-result.md)
- [Configuration draft screen 01 result](../../evals/wrench-local-acceptability/local-config-review-draft-screen-01-result.md)
- [Frontier-token readiness gate](../../evals/wrench-local-acceptability/frontier-token-readiness.md)

All reported screens use development/synthetic material. None establishes
held-out generalization, production utility, or real-task acceptability.
