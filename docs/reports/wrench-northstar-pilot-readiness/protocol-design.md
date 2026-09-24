# North Star pilot readiness protocol

Goal: [pilot readiness](../../goal/wrench-northstar-pilot-readiness/GOAL.md)
Task: choose the first customer-validation, corpus, and outcome-oracle path
Worker: root orchestrator
Date: 2026-09-24 (America/Edmonton)
Job: `W2-NS-OPTIN-PILOT-PROTOCOL-20260924`
Nonce: `OPTIN-PILOT-5A17`
Baseline: `ee294938a63ed9e15b21890e115d3461c1c92276`
Status: proposal drafted and independently reviewed; owner decisions remain open

## Decision

Choose per-task opt-in OpenCode workflows on participant-authorized local
repository snapshots as the eventual primary real-task corpus. Keep early
examples development only, separate from authored fixtures, and do not train
on them. Do not use ARB as a Wrench task-success corpus. For the first utility
comparison, use task-specific predeclared checks plus an independent blinded
reviewer; record user-reported completion separately. The chosen task families
are repository localization and failing-test/log triage. Tool/context choices
are component traces inside those tasks, not an independent outcome oracle.

The next customer evidence should be six non-leading walkthrough interviews
with developers who recently used OpenCode for coding work. A proposed
directional screen is four of six reporting the same recurring context problem
across at least two recent tasks, with an observable workaround or cost. This
is a small qualitative screen only. The gate needs owner approval and does not
measure prevalence, willingness to pay, or Wrench utility.

## Repository evidence

- The North Star describes the target user and context-preparation pain, while
  explicitly stating that demand, support effort, and core-release funding
  remain unvalidated (`docs/northstar/README.md`, product thesis and value).
- The experiment proposes localization, failing-test/log triage, tool/context
  selection, varied repositories/languages, predeclared run manifests, paired
  success, full accounting, and zero safety failures
  (`docs/northstar/V2_EXPERIMENT.md`, stages, pilot, and accounting gates).
- The data-source plan recommends opt-in local workflows and separate
  fixtures, but does not implement capture. Its ARB subsection is stale:
  current monolith/bundle claims conflict with the committed
  [ARB source audit](../../reports/wrench-e0-arb-benchmark-admission/arb-source-audit.md).
  Owner file `docs/northstar/DATA_SOURCES.md` was inspected but not edited.
- Receipt v2 now links post-task references separately, but
  [its evaluation](../../evals/wrench-e0-outcome-receipt/postrun-join-v2.md)
  confirms that references and verification claims remain caller-supplied,
  unpersisted, and unauthenticated.
- The North Star has no recorded user interviews, observed Wrench workflows,
  matched utility, repeat use, switching behavior, support-hour evidence, or
  completed sustainability commitment. Those claims remain hypotheses.

## Limits and handoff

This is a protocol proposal only. No participant was contacted, no consent was
obtained, no repository snapshot was accessed for research, and no capture,
client install/run, provider/model call, training, benchmark download, or
utility test occurred. Retention/deletion deadlines, participant/repository
authorization, consent wording, external-provider disclosure, verifier
independence, and powered E4 margins require owner decision before data
collection. The six-interview gate is proposed, not committed.

Independent review found no material mismatch between this proposal and the
current E0/E4, consent, storage, and evidence boundaries. See the linked
evaluation. Next: owner reviews the proposed discovery screen and consent,
retention, and deletion terms before any participant-facing step.
