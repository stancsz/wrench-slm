# Small local SLM direction closure

Goal: [Measure acceptable local work](../../goal/wrench-local-acceptability/GOAL.md)
Date: 2026-09-26
Status: closed by owner decision
Decision owner: human product owner

## Decision

Stop pursuing a small local SLM as the primary OpenCode agent or semantic
controller for the intended Wrench workflow. The tested Qwen 0.8B route did not
meet the project's semantic acceptance gates across repeated synthetic
screens. Its failures include missing required evidence/tool use, invalid
outputs, unsupported answers, and false abstentions. This direction is not a
feasible use of the current project's effort and constraints.

The pasted discussion about 2B models informed the owner's judgment but is
not experiment evidence. Wrench did not test a 2B model. The conclusion is a
scoped product decision about the proposed small-model OpenCode role, not a
claim that every model up to 2B fails in every role.

## Findings inventory

| Area | Result | What it establishes |
| --- | --- | --- |
| Deterministic proposal route | 176-case synthetic development screen across six bounded action families passed its frozen proposal targets. | Bounded mechanics only, not completed coding work or utility. |
| Exact line-range reads | 6/6 routes matched; 2/2 executor reads were exact; 4/4 boundary abstentions were correct. | Synthetic operation mechanics only. |
| Review-only patch proposals | 12/12 draft diffs and 9/9 abstention boundaries matched. | Four narrow single-file draft operations on synthetic UTF-8/LF inputs. No repository patch was applied or semantic repair quality measured. |
| Deterministic evidence selection | 5/7 positive evidence cases passed; 4/4 abstention boundaries passed. M3 selected-context inputs fell from 3,204 to 2,816 tokens: 11.64% arithmetic mean and 12.11% ratio-of-sums. | Synthetic prompt-input proxy only; no generated answer or downstream/frontier accounting. |
| Qwen 0.8B tool-backed semantic screen 02 | 0/10 cases passed; 0 required evidence-tool calls; all five task classes scored 0/2. There were five false abstentions and two unsupported localization claims. | No accepted semantic SLM task class. See [run 02](local-slm-run-02.md). |
| Qwen 0.8B configuration fact screen | 0/12 grounded positives, 0/8 correct boundary abstentions, 20/20 invalid outputs. The run consumed 8,141 local tokens and 875.3 seconds. | Rejects this task class for the tested model/runtime; local inference cost only. See the [result](../../evals/wrench-local-acceptability/read-only-config-fact-screen-01-result.md). |
| Configuration edit-review screen | 0/2 attempted cases passed; the run stopped after an unchanged-value proposal without evidence read, then invalid JSON. | No accepted edit-review class. |
| Prompt-only generative screen | 0/12 answerable cases met the exact answer/schema/evidence oracle; 3/6 boundary cases were correctly abstained. | No generative class passed. |
| Failing-test evidence-packet screen | 0/3 positive cases completed and 0/3 boundaries reached before a runner/oracle comparison defect stopped the run. | No acceptance result; exposed fixture quarantined. |
| E0 context integration screen | Five expected mechanics branches were observed, but the required separate orchestrator admission record was absent. | Inadmissible diagnostic, not accepted evidence. |
| Localization tokenizer-only screen 02 | Stopped on runtime-lock hash mismatch before tokenizer loading or case scoring. | No token-reduction or acceptability result; exposed fixture quarantined. |
| Evidence-selection SLM screen | Protocol, fixture, test, and runner were prepared in the working tree, but the screen was not run and separate inference authority remains pending. | No result and no basis to resume this direction. |
| Matched frontier-token measurement | Zero eligible actual matched usage pairs and zero independently verified successful pairs. | Full-lifecycle frontier savings **N/A**, not zero. The 29.03% mixed-ledger fixture arithmetic has caller-declared, untrusted outcomes and is plumbing only. |

OpenCode 2.0.18 was installed at the owner's request, but the configured
localhost:4000 route exposed a mutable gateway with mixed provider/subscription
routes and no pinned local model ID or request mode. Its health endpoint timed
out. No OpenCode model request or provider call was made. No consented matched
utility corpus, authenticated dispatch/usage join, or provider measurement
authority is recorded for this experiment.

The deterministic context screen did not generate task answers or measure
downstream calls. Actual full-lifecycle savings remain **N/A**, not zero. The
results and individual screen limits are also summarized in the
[local-work map](local-work-acceptability-map-20260926.md) and
[frontier readiness review](../../evals/wrench-local-acceptability/frontier-token-readiness.md).

## Closure boundary

This closes the local semantic-controller investigation and its proposed
small-model OpenCode primary-agent route. It does not accept E0-E4, establish
real-work utility, or reject the separate deterministic context-preparation
hypothesis. No model, client, or provider run was performed for this closure.
Future work outside this direction would require a new owner decision and a
separately authorized, preregistered experiment.
