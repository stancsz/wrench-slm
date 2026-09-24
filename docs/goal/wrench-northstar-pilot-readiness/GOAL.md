# North Star pilot readiness

Status: protocol proposed; no participant or repository data authorized
Owner: root orchestrator, under human product authority
Job: `W2-NS-OPTIN-PILOT-PROTOCOL-20260924`
Nonce: `OPTIN-PILOT-5A17`
Baseline: `ee294938a63ed9e15b21890e115d3461c1c92276`

## Outcome

Prepare a concrete, reviewable path from the current product thesis to
customer discovery and a future opt-in OpenCode matched-task pilot. The plan
must choose the initial corpus and outcome oracle, separate feasibility from
utility evidence, name all consent and runtime prerequisites, and leave the
human with explicit decisions before any participant-facing or data-capture
work.

This goal does not recruit participants, authorize repository access, capture
data, install or run OpenCode, run a provider, download a benchmark, train a
model, or claim customer demand or utility.

## Proposed decisions

- First customer evidence: structured walkthroughs with developers who have
  used OpenCode for recent coding tasks. Ask about the last concrete task and
  actual workarounds, not hypothetical willingness to use Wrench.
- First real-task corpus: newly collected, per-task opt-in OpenCode workflows
  on participant-authorized local repository snapshots. Keep it development
  only. Keep authored fixtures in a separate stratum. Do not use ARB as an
  outcome corpus or training source.
- First task families: repository localization and failing-test/log triage.
  Record tool/context selection as a component decision trace inside those
  tasks; it has no independent task-success oracle.
- Outcome oracle: freeze task-specific acceptance checks before replay. For a
  code change, require relevant predeclared checks on a clean task snapshot and
  an independent reviewer blinded to the arm to confirm the result matches the
  task and has no out-of-scope changes. Keep the participant's completion
  report separate. Missing, flaky, irrelevant, or ambiguous checks produce
  unknown/inconclusive evidence, not an inferred success.
- First comparison: the direct downstream baseline versus the deterministic
  Wrench path using the same pinned downstream model, task, snapshot, budget,
  and verification policy. Randomize/counterbalance arm order and use clean
  worktrees. No learning during this comparison.

These choices define a development protocol, not a commitment to collect,
retain, transfer, train on, or publish anyone's data.

## Customer discovery screen

The customer and job remain hypotheses. No observed Wrench users, matched task
outcomes, repeat use, switching behavior, support burden, or sustainability
commitment is recorded in the current evidence.

Proposed next evidence is six non-leading task walkthroughs with qualified
OpenCode developers. Each session should reconstruct exactly two recent real
coding tasks from the prior 30 days and identify the actual context work,
existing alternative, delays, retries, and verification. Do not ask
participants to provide repository content or sensitive materials during this
discovery screen. The planned denominator is six participants and twelve task
episodes; report incomplete episodes separately.

Proposed directional gate, pending owner approval: advance to a reversible
pilot only if at least four of six independently describe the same recurring
context problem from at least two recent tasks and identify an observable
workaround or cost. One or fewer weakens this narrow problem-frequency
hypothesis; two or three is inconclusive. This small qualitative screen cannot
estimate market prevalence, willingness to pay, or product utility.

### Eligibility, episode coding, and counterexamples

Recruit six completed interviews from developers who used OpenCode for at least
three coding tasks in the last 30 days and can reconstruct two of those tasks.
Do not require that they report a context problem. Track the denominator as
invited, screened, eligible, enrolled, and completed; report refusals and
incomplete interviews without replacing them silently. The directional gate
uses six completed eligible interviews and is inconclusive if fewer complete.

Code each reconstructed task as one episode, separately for each participant.
Record task family, the information needed, where it was found, the existing
workaround, observable delay/retry/call cost if recalled, how completion was
checked, and whether the episode is specific enough to verify. Assign one or
more problem categories only when supported by the episode narrative. Preserve
"no context problem," "no workaround/cost," "could not recall," and
"not verifiable" as explicit values. Use these predeclared primary categories:
(1) localization of relevant code, tests, or configuration; (2) recovery of a
prior decision or task state; and (3) filtering tool, test, or log output for
task-relevant signals. "Other" remains exploratory and cannot satisfy the
directional gate. A second reviewer should independently code the anonymized
episode summary, resolve disagreements under a recorded adjudication rule
before applying the gate, and retain original codes and rationale.

Count the directional signal per participant, not per episode: a participant
supports a category only when at least two distinct episodes show that same
problem and at least one has a concrete workaround or cost. Report the full
participant/category counts and episode denominator. Include disconfirming
episodes in the report; do not use episode volume to inflate the six-person
denominator or present this screen as a prevalence estimate.

## Capture, consent, and split gates

Before any real-task capture, a human-approved protocol must specify:

- Affirmative per-participant and per-task opt-in, authorized repository/task
  access, capture fields, evaluation versus training use, local storage,
  external model/provider disclosure, review, withdrawal, retention deadline,
  and deletion of raw and derived records.
- No secrets, credentials, hidden reasoning, unrelated conversation, or
  unsolicited repository traversal. Raw prompt/source bytes are not captured
  by default. Any exception needs separate explicit scope and review.
- A bounded local store with tested export, review, delete/reset, expiry, and
  recovery behavior. The current outcome join is in-memory and does not
  authenticate referenced evidence or implement deletion.
- A lineage manifest binding consent version, permitted use, participant/task
  IDs, repository origin group, snapshot and evidence hashes, task family,
  timestamps, redaction/review state, outcome/verifier references, split, and
  deletion status.
- Repository origin/fork, related task family, and time-aware group splits.
  The development pilot cannot be promoted into the sealed final set or used
  to tune against it. Evaluation consent does not imply training consent.
- An independent verifier that resolves each post-task evidence reference
  and checks its task/run/snapshot association. A caller-supplied receipt flag
  alone is not evidence of truth or reviewer independence.

## Acceptance and remaining gates

- The source choice, task families, task-specific oracle, comparison design,
  and consent/deletion prerequisites are explicit and reviewed.
- The customer thesis is marked as unvalidated and the discovery screen is
  directional, with the threshold identified as a proposal for owner approval.
- No participant or repository data is collected and no utility, adoption, or
  training claim is made.
- A later powered utility study still needs the owner to predeclare success
  non-inferiority margin, meaningful cost/time improvement, sample-size and
  power rationale, stopping rules, and promotion decision threshold.
- The E0 client/provider serializer and tokenizer, dispatch failure behavior,
  lifecycle accounting, persistent consented capture, and recovery remain
  open. The three-client E4 stage remains unchanged.

## Evidence and next action

See [protocol design report](../../reports/wrench-northstar-pilot-readiness/protocol-design.md)
and [independent evaluation](../../evals/wrench-northstar-pilot-readiness/review.md).

### Customer-discovery interview kit

The proposed six-interview screen now has a concrete [moderator packet](../../reports/wrench-northstar-pilot-readiness/customer-discovery-interview-kit.md)
and [evaluation](../../evals/wrench-northstar-pilot-readiness/customer-discovery-interview-kit.md).
The packet fixes selection to the two most recent eligible tasks, uses neutral
walkthrough questions, records cumulative screening counts and two separate
episodes per participant, preserves counterevidence, and defines coding and
adjudication. Its consent/privacy opening is explicitly a draft requiring owner
approval. Independent prompt, privacy, and QA reviews found issues in the first
draft; those were repaired and the final artifact passed review at the recorded
hash.

This acceptance is for a reviewable instrument only. The goal remains
proposal-only: it does not approve recruitment, participant-facing use,
recording, note retention, repository/task capture, external transfer,
evaluation, training, publication, or a market/utility claim. Next, the owner
reviews and decides on the six-completed-interview screen, eligibility and
directional threshold, recruitment and compensation, approved note fields and
audience, consent wording, storage/access, retention, withdrawal and deletion
behavior, and any organizational authorization. Participant contact or data
collection must wait for those decisions and tested handling. In parallel,
engineering may continue reversible offline E0 work under its existing
authority.

### E4 owner decisions

The concise [E4 owner decision checklist](../../reports/wrench-northstar-pilot-readiness/owner-decision-checklist.md)
maps the unresolved preregistration fields to the current proposal and review.
It records no approvals, participant activity, or E4 utility evidence; full E4
remains gated on the frozen protocol, accepted upstream stages and client
integrations, and owner-approved rights, study, and operating controls.
