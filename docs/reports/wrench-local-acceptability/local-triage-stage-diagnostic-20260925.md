# Local log-triage stage diagnostic

Date: 2026-09-25 (America/Edmonton)

- Goal: [Measure acceptable local work](../../goal/wrench-local-acceptability/GOAL.md)
- Job ID: `W2-LOCAL-TRIAGE-STAGE-DIAGNOSTIC-20260925`
- Nonce: `LTSD-84A1`
- Inspected revision: `3c9cb277a311e705e225c9322fd3f0d6bdd3ff2f`
- Scope: receipt and source reconciliation only; no inference or rerun

## Result

The exposed two-case failing-log pair separates local retrieval from semantic
task completion:

| Stage | Passed | Result |
| --- | ---: | --- |
| Deterministic route and executor return the exact requested log observation | 2/2 | Exact operation mechanics passed on these synthetic cases. |
| Qwen makes the required evidence-tool call | 0/2 | Both cases stopped before obtaining evidence. |
| Qwen completes log triage with the exact answer and grounded evidence | 0/2 | Both outputs were invalid abstentions, not escalations. |
| Prohibited actions or source mutations | 0 | No violation was recorded. |

This means exact log retrieval is inside the measured local operation envelope.
Semantic error classification and completion by the current SLM are outside it.
The deterministic receipt records successful `read_file` route/executor
observations; it does not produce the semantic answer. Do not count its 2/2
operation passes as 2/2 completed triage tasks.

## Reconciliation method

The canonical manifest digest is
`871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`; both
saved receipts declare this exact digest. Receipt file hashes are:

- Deterministic operation receipt:
  `6b3ea4dfd9653e12f8e2bb3a01c5a098825738634e07ae95f85bae8b37af2db5`
- Local SLM run 02 receipt:
  `d2cce0fd3dee7a420cffa23e9f8f4bc8bb24368dab842353de8c85fce43598f8`

The joined cases share pair ID `triage-error-type` and case IDs `triage-a` and
`triage-b`. I derived the answer from each manifest's exact
`logs/failure.log` bytes, independently of its expected-answer field, by
extracting the literal exception prefix required by the fixture's
`log_error_type` rule. The deterministic receipt's evidence digests match the
corresponding source logs. The independently derived oracle answers are
`TypeError` for `triage-a` and `ValueError` for `triage-b`, each on one exact
line. Both deterministic receipt rows report exact route and executor
observations and a passing operation case.
Both SLM rows report zero tool calls, invalid response schema, no answer
correctness or grounded evidence, and `case_pass=false`.

The SLM used 267 input plus 25 output tokens per case (534 input and 50 output
across this pair), with about 7.8 seconds per response and zero tool time.
This is local model cost only. Frontier calls and eligible usage pairs are
zero, so frontier savings are **N/A**.

## Scope and decision

This is a retrospective join over an exposed, open-development synthetic
fixture, not a preregistered matched-prompt comparison or held-out estimate.
The deterministic request asks for a file read, while the SLM request asks for
the semantic error type. The deterministic operation is therefore evidence
acquisition only; this comparison does not show that deterministic Wrench
completes log triage. It also does not support training or tuning on these
cases, real-work utility, or generalization.

Current acceptance decision: retain exact file read, line-range read, literal
search, and the four explicitly bounded review-only draft operations as
synthetic mechanics-only scope. Keep semantic SLM task acceptance at **0 task
classes**. Training remains stopped. The [independent reconciliation
evaluation](../../evals/wrench-local-acceptability/local-triage-stage-diagnostic-20260925.md)
records the review finding, correction, and limits.

Next measurement should be a fresh, independently reviewed, tool-backed
synthetic holdout for one narrow task class. Require every case to produce the
exact outcome, cite evidence from the actual allowed tool result, correctly
abstain or escalate on its frozen boundaries, and record zero prohibited
actions. Keep its completion rate distinct from tokenizer reductions and from
frontier savings.
