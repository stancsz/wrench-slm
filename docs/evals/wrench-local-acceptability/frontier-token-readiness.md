# Frontier-token measurement readiness review

Date: 2026-09-25. Review revision before this report: `8498941`.

## Decision

**Observed frontier-token savings remain N/A.** There are no eligible matched
baseline/Wrench frontier-usage pairs. Do not interpret the ten-case local SLM
run's 3,059 local tokens as frontier savings, or the deterministic route's
10/10 fixture mechanics as a utility result.

## Existing measurement path

`tools/report_paired_frontier_savings.py` is the strongest existing savings
calculator. It validates supplied outcome-receipt digests and schemas,
requires matching declared protocol, client, frontier-model and token-
convention identities, joins both arms to the declared task snapshot,
reconciles exact input/output usage across frontier attempts and work calls,
excludes incomplete or mismatched pairs, and reports the per-task arithmetic
mean plus ratio-of-sums. Failed task outcomes remain in the token totals and
their outcome counts stay separate from savings. The checks do not authenticate
telemetry or prove prompt/information parity, protocol correctness, arm
configuration or outcome truth; those must be frozen and independently
verified outside the calculator.

This change adds per-task rows with exact arm totals, the task's percentage, or
an explicit exclusion reason. The row uses `task_ref_sha256`, a stable hash of
the task key, so rows can be reconciled without repeating the raw task ID.
This is a pseudonymous reference, not a guarantee against guessing or
cross-report linkage.
Synthetic test receipts exercise the arithmetic and excluded-row behavior;
they are not eligible metric data.

The reporter is a validator/aggregator, not a producer. No current authorized
corpus supplies complete matched receipts. The existing E0 accounting receipts
are caller-supplied fixture evidence, use fixture serializer/tokenizer
callbacks, and explicitly leave downstream outcome and provider accounting
unknown. The local SLM run has no frontier calls at all. Its frontier savings
field is correctly null.

## Data, identity and authority gates

- The only currently admitted task corpus is the Wrench-authored ten-case
  open-development synthetic seed. It is mechanics-only, not a real-work
  utility corpus. The edge-case bundle is regression-only. No participant-
  opted, repository-authorized matched utility data is admitted.
- The first integration is OpenCode 2.0.15, but its configured endpoint on
  localhost:4000 is a gateway. The last recorded active route was force-mode
  OpenRouter with the `minimax/minimax-m3` alias. The alias/state is mutable;
  neither an immutable served revision nor an exact matching client-side
  tokenizer is pinned. A localhost URL is not local inference.
- The OpenCode hook has not dispatched a Wrench-prepared prompt to a downstream
  model. Offline composition and request-lowering fixtures do not establish
  provider-wire or tokenizer parity.
- `COLLABORATION_CONTRACT.json` gives no monetary budget and prohibits provider
  or model calls, client execution, and real-task capture/transfer without
  separate authority. No provider request or capture was made in this review.

These constraints mean a percentage cannot be filled in honestly today.
Changing the denominator to local Qwen tokens, word estimates, fixture
tokenizers, or hand-counted source bytes would make the result look numeric
without measuring the selected frontier route.

## Next valid sequence

1. Preserve the current zero-pair report as N/A. Keep run 01 harness-invalid,
   run 02 synthetic-only, and the 10/10 deterministic result mechanics-only.
2. Freeze a named OpenCode request route, model identity, request/token
   accounting convention, Wrench arm/config identity, baseline arm, retries,
   and task outcome oracle before collecting calls. Unknown or uncorrelated
   usage remains excluded, never zero.
3. For a real-work claim, obtain explicit source/repository authority,
   participant and per-task opt-in, local capture/storage/retention/withdrawal/
   deletion approval, independent outcomes, and a frozen split before replay.
   External provider transfer and its monetary/quota cap need separate approval.
4. Only after those gates pass, produce one receipt per arm/task and feed them
   to the paired reporter. Publish every valid task percentage, the arithmetic
   mean and valid-pair count, ratio-of-sums, all exclusion reasons, task
   outcomes, latency, local cost and resource use. Keep failed tasks in token
   accounting and do not call token reduction useful when task success regresses.

The pre-existing [Northstar pilot-readiness goal](../../goal/wrench-northstar-pilot-readiness/GOAL.md)
contains the detailed proposed participant, consent, oracle, and outcome
requirements. This review adds no approval and authorizes no external action.

## Review and verification

Read-only audits were completed by `token_accounting_audit`,
`corpus_oracle_audit`, and `matched_metric_design` at base revision `8498941`.
Their findings were integrated by the root orchestrator; they did not run
provider requests, capture data, download a corpus, or edit files.

For the per-task reporter change, Python `py_compile` and `git diff --check`
passed. Five focused test functions were directly invoked under Python 3.13:
the two-mean arithmetic example, missing usage, malformed arm shape, malformed
receipt shape, and estimated usage all passed. A separate standard-library
smoke used two in-memory pairs (50% and 0%) plus one excluded pair, yielding a
25% arithmetic mean and 5% ratio-of-sums. The focused pytest file could not
run because `pytest` is absent from both available Python installations. No
real or synthetic usage receipts were processed by the changed reporter
during this verification. A separate read-only critic reviewed the final
reporter changes and their accounting/authority caveats; no material issues
remained.
