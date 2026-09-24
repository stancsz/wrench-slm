# OpenCode developer discovery interview kit

Goal: [North Star pilot readiness](../../goal/wrench-northstar-pilot-readiness/GOAL.md)
Task: turn the proposed six-interview screen into a reviewable moderator packet
Owner: North Star pilot-readiness supervisor
Date: 2026-09-26 (America/Edmonton)
Job: `W2-NS-PILOT-INTERVIEW-KIT-20260926`
Nonce: `PILOT-SUP-6D2F`
Baseline: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`
Status: draft for owner review; not approved for participant use

## Purpose and boundaries

This packet makes the existing proposal for six OpenCode developer walkthroughs
operational. It is designed to find out how recent coding work actually went,
including cases where context handling was not a problem. It does not establish
market prevalence, willingness to pay, product utility, or authorization to
collect data. The directional threshold in the goal remains a proposal pending
owner approval.

Do not schedule or conduct these interviews from this draft. The owner must
approve the opening, note fields, handling and retention terms, recruitment
screen, and directional decision gate first. No participant, repository, task,
prompt, or employer data was collected while preparing this document. This
packet does not request repository access, recordings, prompt/source text,
screenshots, logs, credentials, hidden reasoning, or provider transcripts.

## Moderator preparation

The proposed screen is six completed eligible interviews. Eligibility is based
on OpenCode use for at least three coding tasks in the preceding 30 days and
ability to reconstruct two; do not screen for a reported context problem.
Each interview reconstructs two distinct tasks from that period. Track invited,
screened, eligible, enrolled, completed, refused, and incomplete counts; keep
reasons broad and optional. Do not silently replace incomplete interviews or
change the denominator.

Before any participant-facing use, the owner must resolve the review fields in
the draft opening below, approve an appropriate note-taking/storage process,
and approve retention, withdrawal, deletion, and any permitted downstream use.
If approval is not in place, stop at protocol review. The moderator should have
only this script and a blank copy of the structured note fields available.

Suggested duration is 35 to 45 minutes: opening and eligibility (5 minutes),
two task reconstructions (12 to 15 minutes each), then a closing question (3 to
5 minutes). The moderator should not demonstrate Wrench, describe a proposed
solution, or ask whether the participant would use or pay for it. Avoid praise,
correction, or signaling that a particular answer is desired. Ask the base
question first; use only neutral probes when the detail is missing.

## Draft opening for owner approval

> **DRAFT ONLY. OWNER APPROVAL REQUIRED BEFORE USE.**
>
> Thanks for considering this conversation. We are trying to understand how
> developers handle information while completing coding tasks with OpenCode.
> We are interested in both cases where finding or managing context was
> difficult and cases where it went smoothly. There are no right answers, and
> please do not share code, repository names, prompts, logs, screenshots,
> credentials, employer-confidential details, or anything else you are not
> comfortable discussing at a high level.
>
> This conversation is intended to cover two recent tasks by description only.
> **[OWNER: specify exactly what notes, if any, may be taken and who can see
> them.]** **[OWNER: specify whether the notes may be used only for product
> discovery, and confirm that they will not be used for model training or
> evaluation.]** **[OWNER: state the approved storage location, retention
> deadline, withdrawal route, and deletion process for notes and summaries.]**
> **[OWNER: state whether the conversation will be recorded. Default in this
> draft is no recording.]** You can skip any question or stop at any time.
>
> Before we begin, do you agree to take part under those terms? It is fine to
> say no. Do you have any questions about what will be noted or how it will be
> handled?

Do not present the bracketed text as settled policy. If terms are unanswered,
inconsistent with the approved protocol, or not understood by the participant,
do not proceed. Consent to an interview would not grant repository access or
authorize capture, transfer, evaluation, training, or publication of task data.

## Moderator script

### Eligibility and neutral task selection, without problem screening

1. “In the last 30 days, about how many coding tasks have you worked on using
   OpenCode?”
2. “Thinking only of the order they happened, what were your two most recent
   coding tasks using OpenCode in that period? Please keep the descriptions
   general and do not show me any materials.”
3. “Can you reconstruct what happened in each of those two tasks from memory,
   without showing me code, prompts, files, or other materials?”

Record only whether the predeclared eligibility conditions are met. If fewer
than three tasks, mark ineligible and end politely. Start with the two most
recent tasks in chronological recency order. If either cannot be recalled well
enough to reconstruct, do not substitute an older task based on whether it
sounds relevant; mark the interview ineligible or incomplete under the approved
screening rule. Do not ask whether the person had context problems to determine
eligibility.

### Task episode A, then task episode B

Use the same sequence for both episodes, in recency order, on the two tasks
already selected in the eligibility step. Do not substitute another task
because it sounds more relevant to Wrench's target problem. Ask one open
question at a time and let the participant narrate in their own terms.

1. “For this task, what were you trying to get done?”
2. “Starting from when you began, what happened next?”
3. “What information did you need along the way, and how did you find it?”
4. “What did you do next?”
5. “Did anything cause you to change your plan or try a different approach?
   If so, what happened?”
6. “How did that fit into the rest of the task? Did it affect anything else,
   or not?”
7. “How did the task end? Was anything left unfinished?”
8. “If you considered it complete, how did you decide it was done? What did
   you check?”
9. “Was there anything that went smoothly or took less effort than you
   expected?”
10. “Is there anything important about this task that I have not asked?”

If recall is vague, use neutral probes such as “What do you remember doing
next?”, “What makes you say that?”, “How did you know?”, or “Was there a
different way it could have gone?” Do not list target problem categories as
prompts. Do not ask for exact call counts, token use, durations, prices, or
content. If the participant spontaneously describes time or cost, capture only
an optional coarse category (`no added effort reported`, `a few minutes`,
`tens of minutes or more`, `unknown`, `not discussed`); do not record exact
units, amounts, service names, or distinctive comparisons. Treat these as
participant estimates, not measured observations.

### Closing

“Across those two tasks, what was most different between them?” and “What did I
miss or misunderstand?” Summarize the participant's account at a high level
and invite correction. Do not pitch Wrench or ask for a hypothetical adoption
or pricing judgment in this screen.

## Structured notes

Use one participant row and two episode rows. Assign a study-only random ID
after approval; do not write a name, handle, email, employer, repository, branch,
issue, or exact date into analytic notes. If administration requires contact
details, keep them in a separate approved system with a separate access policy
and deletion schedule. Do not record raw quotations unless the owner approves
that field and its handling; concise paraphrases should omit identifying
details.

### Participant-level accounting

| Field | Allowed value or instruction |
|---|---|
| Study ID | Random code; no direct identifier in analysis notes |
| Recruitment status | Screened / ineligible / eligible / enrolled / completed / refused / incomplete / withdrawn |
| OpenCode coding tasks, prior 30 days | `3+` / `<3` / unable to recall / not asked |
| Two episodes reconstructable | yes / no / uncertain |
| Interview disposition | completed / incomplete / declined / ineligible / stopped |
| Broad incomplete/refusal reason | optional, nonidentifying, or declined |
| Consent protocol version and affirmative response | Record only under owner-approved process |
| Notes review / withdrawal / deletion state | pending / complete / withdrawn / deleted, using approved process |

Maintain a separate aggregate funnel tally, updated once for every person at
each reached stage, because a single current status cannot reproduce stage
counts. Record counts for invited, screened, eligible, enrolled, completed,
refused, incomplete, and withdrawn. A person may count in successive stages;
report each count and the flow between stages without treating refusals or
incomplete interviews as completed. Store no identifying reason in this tally.

### Episode-level reconstruction

| Field | Entry guidance |
|---|---|
| Episode ID and order | Study ID plus A or B; no external task identifier |
| Recency | Within prior 30 days: yes / no / uncertain; avoid exact date |
| Task family | Localization / failing-test-or-log triage / other / unclear |
| Intended result | High-level paraphrase; no code or proprietary task text |
| Information needed | High-level types only; never paste source, prompt, output, or logs |
| Where information was found | Participant-described tool/source category, generalized |
| Sequence and workaround | Concise factual paraphrase, including no workaround |
| Friction observed or recalled | None / search / missing context / reconstruction / filtering / repeat / other / uncertain |
| Time, retries, or call cost | None reported / coarse participant estimate (`a few minutes` or `tens of minutes or more`) / unknown / not discussed; never retain exact units or amounts |
| Verification | High-level check type and whether result was checked; no evidence artifact capture |
| Outcome account | Participant says complete / incomplete / abandoned / unclear; self-report only |
| Specificity | Sufficient for high-level coding / insufficient / could not recall |
| Sensitive or identifying detail volunteered | Do not transcribe; pause, redact/delete any captured segment under the approved procedure, and record only “redirection needed” |
| Moderator correction | Participant correction or nuance, paraphrased |
| Counterevidence | Smooth handling, no problem, workaround was cheap/effective, task unlike target, or other contradiction |

## Coding and adjudication

Code the episode narrative, not participant identity or enthusiasm. The primary
categories are fixed by the goal:

1. **Localization:** difficulty finding relevant code, tests, or configuration.
2. **State recovery:** difficulty recovering a prior decision or task state.
3. **Output filtering:** difficulty isolating task-relevant information from
   tool, test, or log output.

Use multiple categories only when the narrative supports each independently.
Use `other` as exploratory only; it cannot satisfy the directional gate.
Always code the counter-signals explicitly: `no_context_problem`,
`no_workaround_or_cost`, `could_not_recall`, and `not_verifiable`. These may
coexist with a category when an episode contains mixed evidence. Do not infer
cost from frustration or infer success from a participant's confidence.

For each episode, the primary coder records category codes, evidence paraphrase
supporting each code, counter-signals, specificity, and confidence
(`clear` / `mixed` / `weak`). A second reviewer independently codes the same
anonymized, minimized episode summary without seeing the first codes. Preserve
both initial code sets and rationales. For disagreements, the two reviewers
compare only the approved summary, document the point of disagreement and
reasoning, and record an agreed code or `unresolved`; if they cannot agree,
retain the unresolved state and count it as not supporting the gate. Do not
rewrite episode notes to make agreement appear stronger.

Apply the proposed participant-level directional rule only after coding is
locked: a participant supports a predeclared category when that same category
is supported in both distinct episodes and at least one episode has a concrete
workaround or cost. Count at most once per participant per category. Show the
full six-participant denominator, completed and incomplete episodes, category
counts, `other`, unknowns, unresolved disagreements, and disconfirming cases.
The proposed threshold of at least four of six participants for one repeated
category is directional and awaits owner approval. One or fewer would weaken
this narrow problem-frequency hypothesis; two or three or fewer than six
completed eligible interviews is inconclusive. None of these outcomes proves
prevalence, willingness to pay, adoption, or task utility.

## Disconfirming evidence to preserve

Record and report evidence that could weaken the proposed customer/job thesis,
including:

- The participant readily found needed information or did not experience a
  recurring context problem across either task.
- Existing search, navigation, notes, shell commands, IDE features, or normal
  model context handled the task with little extra effort.
- A reported delay or retry was caused by another factor, or the participant
  could not connect it to context work.
- The two episodes involved different problems, or the same issue appeared
  only once without a concrete workaround or cost.
- The task was too unusual, simple, or poorly recalled to support a specific
  category; mark it `other`, `could_not_recall`, or `not_verifiable` as apt.
- The participant describes context tools as adding setup, latency, confusion,
  or maintenance burden, or says they would rather keep the current workflow.
- The account conflicts with another part of the same interview or cannot be
  distinguished from hindsight; retain the ambiguity.

Do not convert a workaround mention alone into demand for Wrench. Keep the
actual alternative and its cost or benefit visible, including when no change
appears useful.

### Accidental sensitive disclosure procedure

No recording is planned in this draft. If the owner separately approves a
recording, the protocol and opening must be revised to say so and must describe
access, retention, withdrawal, and deletion before any session. If a participant
begins sharing code, a secret, credentials, identifying task details, or other
sensitive information, gently interrupt and redirect to a high-level account.
Pause any recording immediately. Do not type or repeat the detail. If it was
captured in notes or recording, stop the session's note-taking or recording;
remove the affected text or segment from the working copy and every controlled
copy, then verify removal before resuming. If the recording cannot be reliably
edited and verified, do not retain it; end the session if necessary. If a
withdrawal or deletion request arrives, pause use of the affected notes and
follow the approved request route and deadline for deleting both notes and
derived summaries. Do not promise deletion behavior until the owner has
approved and tested the actual storage and recording workflow.

## Owner decisions before use

1. Approve, revise, or reject the proposed six-completed-interview screen, its
   eligibility rules, and its directional 4-of-6 threshold.
2. Approve the participant-facing opening and note fields, including whether
   interviews may be summarized or quoted. Recording is off by default; any
   recording requires an explicit owner decision and a revised tested handling
   and deletion procedure before use.
3. Set access controls, storage location, retention deadline, withdrawal path,
   deletion behavior for notes and derived summaries, and the handling of
   accidental sensitive disclosures.
4. Approve recruitment, compensation if any, and any organizational/employer
   authorization requirements before contact.
5. Keep any later repository/task capture, external provider disclosure,
   evaluation, training, transfer, or publication decision separate. This kit
   grants none of them.

## Limits and handoff

This is an interview instrument proposal, not discovery evidence, a consent
form, a legal determination, or data-collection authorization. No external
sources, participants, repository materials, providers, clients, or models were
used. Independent critique and artifact checks are recorded in the linked
[evaluation](../../evals/wrench-northstar-pilot-readiness/customer-discovery-interview-kit.md).
Next: the orchestrator obtains owner decisions before any participant-facing
use and keeps the protocol's capture and utility gates separate.
