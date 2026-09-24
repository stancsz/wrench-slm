# E4 owner decision checklist

Status: open checklist for owner review. This is not a preregistered protocol,
approval record, participant plan, or E4 acceptance.

Job: `W2-NS-E4-OWNER-DECISIONS-20260925`
Nonce: `E4-OWNER-DECISIONS-9B31`
Baseline: `4cffdd28a6e10e35ead5f02bfcd8106946ad4828`
Date: 2026-09-24 (America/Edmonton)

Use this checklist to resolve the fields that the [E4 preregistration
template](../../northstar/E4_PREREGISTRATION_TEMPLATE.md) leaves `TBD`, in
light of the [pilot-readiness
goal](../../goal/wrench-northstar-pilot-readiness/GOAL.md) and its
[independent review](../../evals/wrench-northstar-pilot-readiness/review.md).
The goal proposes an opt-in OpenCode development pilot and a task-specific
oracle approach; the review confirms those remain proposals. No proposed value
below is treated as owner approval. Record decisions and evidence in a frozen
protocol before any sealed-task access or study activity.

## Owner decisions still needed

- [ ] **Study readiness and authority (template §1):** name the study owner and
  reviewers; set its version, date, immutable revision, and window; identify
  accepted E0–E3 and integration evidence by exact revision; document storage
  admission, measured roots, peak reservation, volume free space, host/device
  reserve plan, and the human approval record. Confirm every required upstream
  gate is accepted before considering E4.
- [ ] **Question and decision rule (template §2):** freeze the primary
  question, paired comparison, outcome and unit, uncertainty method and
  clustering, secondary outcomes, non-inferiority margin or minimum
  improvement, multiple-comparison handling, go/no-go/inconclusive rules, and
  mandatory stop conditions. The pilot review says no powered utility margin
  is approved.
- [ ] **Participants, tasks, and power (template §3):** decide target
  population and recruitment, task definitions and exclusions, sampling
  frame/window, participant/task/repository/group counts, pair key, grouping
  and duplicate rules, splits and assignment date, exposure/lineage checks,
  and sample-size or power rationale. The proposed six-interview directional
  discovery screen is not an E4 sample-size decision or utility estimate.
- [ ] **Frozen identities (template §4):** bind each of OpenCode, DeepSeek
  Harness, and Claude Code to its exact accepted integration and version;
  freeze Wrench build/configuration, the hook/API lifecycle point and request
  boundary, each final serializer and tokenizer with revision/settings,
  downstream model/provider
  and endpoint class, adapter identities, prompts/decoding, budgets/truncation,
  local runtime/hardware/precision, and task/source snapshot manifests. Keep
  client-specific serializer/tokenizer identities separate when they differ.
- [ ] **Arms and execution controls (template §5):** specify equivalent
  information/budgets for all four arms; decide order randomization,
  routing/fallback, cache reset/state, concurrency/schedule, retry/repair/
  timeout/cancel/resume limits, held-constant permissions/verification,
  blinding, and nondeterministic-repeat handling.
- [ ] **Outcome oracle and adjudication (template §6):** assign exact
  task-specific oracle versions/hashes and automated/human roles; define
  correct accept/abstain, prohibited accept, and unresolved; name adjudicator
  qualifications/conflict handling, feasible blinding, retained evidence,
  correction/disagreement/unknown handling, validation, and an isolated
  pre-study pilot procedure. The goal's proposed checks and blinded review
  still need frozen identities and an approved protocol.
- [ ] **Full lifecycle accounting (template §7):** define per-task/arm/client/
  cache collection and reconciliation for outcomes, all paid calls and costs,
  local token usage, compute/energy, amortized learning cost,
  auxiliary/tool/verification/retry/fallback calls, latency, resource samples,
  cache/retrieval/artifact activity, missing-data handling,
  denominators/conventions, and immutable logs/receipts. Do not infer missing
  telemetry as zero.
- [ ] **Rights and data lifecycle (template §8):** approve participant
  information and opt-in wording, per-task consent and withdrawal,
  repository/employer/source authorization, capture and excluded fields,
  secret detection/redaction review, local location/access/encryption and
  custodians, retention and deletion/reset verification, any separate
  provider-transfer scope or explicit no-transfer rule, derived-data rights
  lineage, and incident/contact process. The pilot goal names these as gates;
  its review says consent wording and retention/deletion deadlines remain
  undecided.
- [ ] **Sealing and access (template §9):** name the final-set custodian and
  access list; freeze/hash and log access before inspection; define exposure,
  contamination, replacement, pause/restart, partial-evidence preservation,
  monitoring, and emergency-stop procedures. Make mandatory stop conditions
  explicit for authority or consent breach, data leakage, prohibited action or
  unexpected mutation, missing identity or oracle, accounting failure,
  resource or storage boundary breach, and unrecoverable state.
- [ ] **Results and release decision (template §10):** specify the frozen
  protocol, task/run manifests, privacy-safe exclusion/withdrawal counts,
  per-arm/client/stratum outcomes and uncertainty, reconciled cost/resources,
  failures/deviations/missing/inconclusive findings, reviewer sign-off, and
  the human production decision record.

## Gate boundary

Keep every unresolved item open. The proposed OpenCode workflow, task families,
discovery interview screen, and oracle approach do not authorize recruitment,
participant or repository access, capture, provider transfer, evaluation,
training, or publication. This checklist records no participant activity and
no E4 utility result. It is distinct from full E4 acceptance, which still
requires accepted upstream stages, accepted three-client integrations, a
frozen and approved protocol, and completed matched-task evidence.

## Source map

Each checklist item maps to the correspondingly numbered section of
`docs/northstar/E4_PREREGISTRATION_TEMPLATE.md`. The distinction between a
proposal and owner approval, the proposed OpenCode development-pilot scope,
its consent/deletion prerequisites, and the open utility gates come from
`docs/goal/wrench-northstar-pilot-readiness/GOAL.md`. The review's decision
and limits confirm that no recruitment, capture, transfer, training, or
publication was authorized, and that the directional interview threshold,
powered utility margin, consent form, retention/deletion deadlines, and
authorization procedure remain undecided.
