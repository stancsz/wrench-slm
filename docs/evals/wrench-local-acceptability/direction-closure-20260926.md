# Evaluation: small local SLM direction closure

Date: 2026-09-26
Decision: closed by the human product owner
Scope: small local SLM as OpenCode primary agent or semantic controller
Evidence summary: [closure report](../../reports/wrench-local-acceptability/direction-closure-20260926.md)

## Finding

The tested Qwen 0.8B route failed repeated synthetic semantic acceptance
screens: 0/10 on the tool-backed five-class screen, 0/12 grounded positives
and 0/8 correct boundary abstentions on the configuration fact screen, and
0/2 attempted configuration edit-review cases. No semantic task class was
accepted. This supports the owner's no-go decision for this role in the
intended Wrench workflow.

The supplied discussion's general claims about 2B models were not tested by
Wrench and are not treated as measured findings. The decision is scoped to
the proposed small-model role, not a universal parameter-count threshold.

## Measurement boundary

There are zero eligible matched baseline/Wrench frontier-usage pairs and no
independently verified successful pair. Full-lifecycle frontier-token savings
remain **N/A**. The 11.64% synthetic prompt-input reduction and 29.03% fixture
ledger arithmetic are not frontier savings. The deterministic context
hypothesis remains unproven.

## Review record

The orchestrator reconciled the existing goal, run reports, and metric
readiness review, then recorded the owner's explicit direction decision.
This was a documentation closeout, not a new model or client run. No tests or
benchmarks were run for this evaluation. No independent reviewer was used for
this closeout; the referenced run-level evaluations retain their prior review
records.
