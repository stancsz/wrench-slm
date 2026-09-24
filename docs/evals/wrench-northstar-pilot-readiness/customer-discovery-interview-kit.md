# OpenCode developer discovery interview kit evaluation

Goal: [North Star pilot readiness](../../goal/wrench-northstar-pilot-readiness/GOAL.md)
Evaluated artifact: [interview kit](../../reports/wrench-northstar-pilot-readiness/customer-discovery-interview-kit.md)
Evaluator: North Star pilot-readiness supervisor
Date: 2026-09-24 (America/Edmonton)
Job: `W2-NS-PILOT-INTERVIEW-KIT-20260926`
Nonce: `PILOT-SUP-6D2F`
Repository baseline: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`
Final artifact SHA-256: `8BC179BF59D643D6B0C56E366F347E505177BDF94DD914C8A80B3E562E473C8D`
Decision: PASS as a draft for owner review; NOT READY for participant use

## Scope and acceptance

The review checks that the proposed six-interview OpenCode discovery screen
now has a moderator sequence, neutral task selection and prompts, an episode
note schema, cumulative recruitment denominator, explicit codebook and
adjudication, disconfirming evidence, and a consent/privacy opening that is
clearly a draft awaiting owner approval. It also checks that the kit preserves
the proposed status of the 4-of-6 directional gate and does not claim demand,
prevalence, willingness to pay, task utility, or collection authority.

The evaluator inspected the kit against the owning pilot-readiness goal and
North Star thesis, reviewed three independent critiques and their repairs,
re-read the final artifact, and checked its final hash and repository state.
No tests were run because this change is documentation only. No participants,
repository/task data, client, provider, or model were contacted or used.

## Independent critique and repairs

Three depth-2 reviewers performed read-only reviews. The initial critiques
returned **NEEDS_CHANGES** and identified these issues:

- The original sequence named target problem categories and implied a time or
  effort effect. The kit now uses open prompts about task sequence, plan
  changes, effects or no effects, completion, unfinished work, and smooth
  handling without listing the coded categories.
- The original task-selection language allowed the moderator to choose a
  salient example. The final kit asks for the two most recent tasks in the
  previous 30 days, in recency order, and says to use those selected tasks
  without relevance-based substitution.
- The first privacy review asked for operational accidental-disclosure
  handling and coarser cost fields. The final kit makes recording off by
  default, requires a revised owner-approved process for any recording, and
  tells the moderator to pause, omit and remove captured sensitive material,
  verify removal before resuming, and stop if reliable removal is unavailable.
  Time/cost are optional coarse estimates; exact units and amounts are not
  retained.
- The first QA found that a single current recruitment stage would not recover
  the full denominator. The kit now calls for a separate cumulative funnel
  tally for invited, screened, eligible, enrolled, completed, refused,
  incomplete, and withdrawn counts, with stage flow.

| Review responsibility | Reviewer job and nonce | Final decision |
|---|---|---|
| Prompt neutrality and disconfirming evidence | `W2-NS-PILOT-PROMPT-FINAL-20260926`, `PROMPT-FIN-230D` | Earlier review found and drove correction of category cues, an implied effect, and task-selection inconsistency. Final identity check passed; final task-selection wording was directly confirmed by QA. |
| Privacy and data minimization | `W2-NS-PILOT-PRIVACY-FINAL-20260926`, `PRIV-FIN-7B13` | PASS on final artifact hash; recording default, sensitive-disclosure procedure, and coarse optional cost fields were reviewed. |
| Acceptance and artifact QA | `W2-NS-PILOT-KIT-QA-FINAL-20260926`, `KIT-QA-FIN-002C` | PASS on final artifact hash; funnel, final task-selection rule, codebook, gate, draft opening, and limitations were checked. |

After those repairs, the privacy reviewer returned **PASS** on the final hash.
The QA reviewer returned **PASS** on the final hash, including direct
confirmation that the two most recent tasks are used without substitution and
that cumulative stage counts are recoverable. The prompt critic's earlier
review found the precise task-selection inconsistency; after the correction,
its final return rechecked HEAD, storage admission, diff-check, and artifact
identity but did not reread the changed paragraph. The QA reviewer did reread
and verify that paragraph against the final hash. This limitation is retained
so the final content check is attributed accurately.

## Verification evidence

- Final artifact hash: `8BC179BF59D643D6B0C56E366F347E505177BDF94DD914C8A80B3E562E473C8D`.
- All reviewers observed repository HEAD
  `0c7a00ab8cc4970ae66133d51bada7617fb7db90`.
- Storage checker with the npm cache explicitly included reported
  `WITHIN_LIMIT`: 2,280,614,604 actual bytes, 20,103,000 active reservation
  bytes, and 47,699,282,395 bytes headroom. The named 2,000,000-byte
  interview-kit reservation was active during artifact work and review.
- `git diff --check` reported no whitespace errors in the kit. It emitted
  LF-to-CRLF warnings for two unrelated, concurrently edited goal files; they
  were not changed for this task.
- Host-resource snapshot during work: 38.5% system RAM free and 15,185 MiB of
  16,311 MiB VRAM free. No inference, model, benchmark, provider, or other
  resource-heavy job was run by this task.
- Three reviewers honored read-only scope. No participant contact or data
  collection took place.

## Findings and limits

The kit is concrete enough for the owner to review the exact interview flow and
proposed analysis rules. It is not evidence that the problem exists or that
OpenCode developers will adopt Wrench. Six interviews remain a small
qualitative directional screen; it cannot estimate prevalence or utility.

The opening still has owner placeholders for approved notes, audience, use,
storage, retention, withdrawal, and deletion terms. Recruitment, compensation,
organizational authorization, note-taking/recording workflow, and the
4-of-6 threshold need owner decisions. If recording is considered, the actual
workflow must support the promised selective removal or stop and deletion
behavior before the interview can proceed. This evaluation grants no authority
to recruit, contact, record, retain, or collect task/repository data.

## Recommendation

Accept the artifact as a draft for owner review and update the goal's evidence
links. Keep the pilot readiness status proposal-only. Participant-facing use
must wait until the owner has approved the questions, recruitment, data fields,
consent, access, retention, withdrawal/deletion behavior, and decision gate.
