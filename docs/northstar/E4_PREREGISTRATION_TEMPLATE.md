# E4 matched-task preregistration template

Status: protocol template only. This document does not admit data, authorize
capture or evaluation, approve provider transfer, or authorize a model/client
run. Leave unresolved fields marked `TBD`; do not treat a completed form as
approval. Obtain the human approvals listed below before collecting or running
any real task.

Use this template to freeze one proposed E4 study before accessing its sealed
evaluation tasks. E4 is intended to assess matched real workflows across
OpenCode, DeepSeek Harness, and Claude Code after the required upstream stages
and integrations are accepted. A first-client replay is a scoped integration
milestone, not full E4 evidence or full client support.

## 1. Study identity and readiness

- Study ID / version: `TBD`
- Owner and reviewers: `TBD`
- Protocol date and immutable revision/hash: `TBD`
- Planned start/end window: `TBD`
- E0, E1, E2, and E3 acceptance evidence and exact revisions: `TBD`
- Client integrations accepted for this study, with evidence: `TBD`
- Storage admission job ID, peak reservation, measured roots, and volume free-space check: `TBD`
- Host/device and minimum RAM/VRAM reserve plan: `TBD`
- Human approval record for this study: `TBD`

Do not start E4 if a required upstream stage, integration, identity, authority,
resource bound, or recovery condition is unresolved. Missing fields are not
defaults.

## 2. Questions, estimands, and decision rules

- Primary study question: `TBD`
- Primary comparison and estimand (paired task-level difference): `TBD`
- Primary outcome and unit: `TBD`
- Confidence level and paired uncertainty-interval/inference method: `TBD`
- Resampling/inference unit and clustering treatment for participant, repository, and task groups: `TBD`
- Secondary outcomes, explicitly labeled: `TBD`
- Acceptable non-inferiority margin / minimum improvement: `TBD`
- Multiple-comparison handling, if applicable: `TBD`
- Go, no-go, and inconclusive rules: `TBD`
- Conditions that force a stop regardless of average outcome: `TBD`

Do not select or change primary outcomes, margins, exclusions, or stopping
rules after inspecting sealed results. A small or underpowered study is
inconclusive, not a pass.

## 3. Task population, pairing, and splits

- Target participants and recruitment method: `TBD`
- Eligible task families and operational definitions: `TBD`
- Exclusions, including safety-sensitive or out-of-scope tasks: `TBD`
- Sampling frame, sampling method, and date window: `TBD`
- Planned number of participants, tasks, repositories, and groups: `TBD`
- Pair key and rule for ensuring each arm receives the same task, initial state, and permitted information: `TBD`
- Repository/task-group/fork clustering and duplicate detection rule: `TBD`
- Repository, task-family, and time split plan; split assignment date: `TBD`
- Training/development exposure checks and sealed final-set boundaries: `TBD`
- Inheritance rule for paraphrases, derivatives, trajectories, and corrections: `TBD`
- Sample-size or power rationale based on paired outcome variance and the frozen margin: `TBD`

Keep related repositories, forks, task families, near-duplicates, and derived
records in the same split. Do not use sealed final tasks, outcomes, or errors
for training, prompt tuning, threshold tuning, or oracle repair.

## 4. Frozen task and system identities

For each task, freeze and hash the authorized repository snapshot, task
statement, initial agent state, relevant history/tool results, task prompt,
test/oracle inputs, and any source material. Record exact bytes or approved
content-addressed references without placing private source text in this
protocol document.

| Identity | Frozen value or manifest reference |
| --- | --- |
| Client name and version for each of the three integrations | `TBD` |
| Wrench build/source commit and configuration | `TBD` |
| Hook/API lifecycle point and request boundary | `TBD` |
| Final request serializer and tokenizer name, revision, and settings | `TBD` |
| Downstream model/provider identity, revision, and endpoint class | `TBD` |
| Foundation, Wrench-Core, and personal adapter hashes/versions | `TBD` |
| Prompt, system instructions, schemas, and decoding settings | `TBD` |
| Context/token budgets and truncation rules | `TBD` |
| Local model/runtime, hardware, and precision settings | `TBD` |
| Task/source snapshot manifest and hashes | `TBD` |

Record separate identities where a client serializes or tokenizes differently.
An unverified serializer/tokenizer match is unresolved, not assumed equivalent.

## 5. Comparison arms and execution controls

Specify how each arm receives equivalent task information and downstream
budgets. Pin configurations and order randomization before opening the final
set.

1. Downstream model alone with its normal context: `TBD`
2. Deterministic Wrench plus the same downstream/fallback model: `TBD`
3. Wrench plus foundation and frozen Wrench-Core controller and the same fallback: `TBD`
4. Arm 3 plus a personal adapter trained only on prior permitted data: `TBD`

- Task/arm order randomization and counterbalancing: `TBD`
- Provider/local route rules and fallback behavior: `TBD`
- Cold/warm cache definition and reset method: `TBD`
- Concurrency levels and workload schedule: `TBD`
- Retry, repair, timeout, cancellation, and resume limits: `TBD`
- Verification and tool permissions held constant across arms: `TBD`
- Run operator blinding and any unavoidable unblinding: `TBD`
- Repeat policy and treatment of nondeterministic outcomes: `TBD`

## 6. Outcome oracle and adjudication

- Task-specific success oracle and exact version/hash: `TBD`
- Whether oracle checks are automated, human-reviewed, or both: `TBD`
- Correct-accept, correct-abstain, prohibited-accept, and unresolved definitions: `TBD`
- Independent adjudicator qualifications and conflict process: `TBD`
- Blinding of adjudicators to arm/client where feasible: `TBD`
- Evidence retained for each judgment and provenance: `TBD`
- Correction, disagreement, and unknown-outcome handling: `TBD`
- Oracle validation and pre-study pilot procedure, isolated from sealed tasks: `TBD`

Later success alone does not establish which earlier context choice caused the
outcome. Preserve ambiguous cases as unresolved; never force a label to improve
the measured result.

## 7. Outcomes and complete accounting

Define collection and reconciliation for the entire request lifecycle, by
task, arm, client, and cache condition.

- Paired final-task success and uncertainty interval: `TBD`
- Correct eligible accepts, correct abstentions, prohibited accepts, misses, and leakage: `TBD`
- Paid frontier input/output tokens and dollars for every call: `TBD`
- Local token/compute/energy and amortized learning cost: `TBD`
- Tool schemas, title/auxiliary calls, verification, retries, repairs, fallbacks, and context rebuilds: `TBD`
- End-to-end and component latency, including failed/cancelled work: `TBD`
- Resource sampling (RAM, VRAM, CPU, disk, temperature/power if available): `TBD`
- Cache state, retrieval misses/page faults, and artifact-store activity: `TBD`
- Missing-telemetry rule and reconciliation method: `TBD`
- Denominators, tokenizer/usage conventions, and cost conversion: `TBD`
- Logging schema, clock source, collection owner, and immutable receipt hashes: `TBD`

Report frontier-token savings, Frontier Token Share, final-task success,
dollars, latency, and local costs separately. Do not infer unobserved calls or
resource use as zero. Report by client and task stratum; do not hide failures in
an aggregate.

## 8. Rights, consent, privacy, and data lifecycle

- Participant information and explicit opt-in wording/version: `TBD`
- Per-task consent record and withdrawal procedure: `TBD`
- Repository owner/employer/source authorization and permitted-use evidence: `TBD`
- Approved capture fields and explicitly excluded fields: `TBD`
- Secret/private-data detection and redaction review: `TBD`
- Local storage location, access controls, encryption, and named custodians: `TBD`
- Retention schedule and deletion/reset verification procedure: `TBD`
- Provider/model transfer scope and separate approval, or explicit no-transfer rule: `TBD`
- Rights and consent lineage for derived labels, traces, logs, and reports: `TBD`
- Incident handling and participant contact path: `TBD`

Public visibility does not itself grant collection, training, or transfer rights.
Keep private repository data local unless a specific transfer is authorized.
If permission, redaction, or lineage is unresolved, exclude the task and record
the exclusion without retaining disallowed content.

## 9. Sealing, access, and stopping

- Final-set custodian and access list: `TBD`
- Freeze/hash procedure and timestamp before any result inspection: `TBD`
- Access log location and review cadence: `TBD`
- Exposure, contamination, and replacement rules: `TBD`
- Mandatory stops: authority/consent breach; data leakage; prohibited action or unexpected mutation; missing identity/oracle; accounting failure; resource/storage boundary breach; or unrecoverable state: `TBD`
- Pause/restart conditions and preservation of partial evidence: `TBD`
- Planned monitoring owner and emergency stop method: `TBD`

Never resume from an exposed or altered final set as if it were sealed. Retire
exposed items and document replacement under a separately frozen plan.

## 10. Results package

- Frozen protocol revision/hash: `TBD`
- Task and run manifest hashes: `TBD`
- Exclusion and withdrawal counts by reason, without revealing private content: `TBD`
- Per-arm, per-client, per-stratum outcomes and paired uncertainty: `TBD`
- Full cost/resource/accounting reconciliation: `TBD`
- All failures, deviations, missing data, and inconclusive findings: `TBD`
- Reviewer sign-off and human production decision record: `TBD`

### Synthetic fixture boundary

The Wrench-authored synthetic matched-task seed may be used only to check
runner mechanics such as pair handling, schema validation, accounting joins,
and report generation. Keep its cases and scores out of E4 utility aggregates,
population estimates, sample-size calculations, and production claims. It is
an open development fixture, not a real-task substitute or sealed holdout.
