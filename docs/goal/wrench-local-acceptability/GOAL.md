# Measure acceptable local work

Status: active; the first deterministic mechanics envelope is measured. A
user-requested, one-run local SLM diagnostic is being prepared; real-work
utility remains unmeasured.

## Objective

Establish which bounded coding-agent tasks Wrench can safely complete locally,
which it should abstain from, and which must be escalated. Measure task quality
and frontier-token effects on matched work before training or promoting a
learned controller.

## Current decision

The current provider-free rule route has a narrow acceptable envelope: bounded
exact reads, literal searches, and source-tied extraction when the requested
fact is present and unambiguous in the supplied snapshot. It must abstain when
required evidence is missing, stale, or ambiguous. It does not establish
general code editing, root-cause diagnosis, or local SLM capability.

The first open-development seed run matched its frozen mechanics/oracle checks
on 10/10 authored synthetic cases: 7 completed answers and 3 correct
abstentions. Results are broken out by class in the [measurement report](../../reports/wrench-local-acceptability/initial-mechanics.md).
This is fixture mechanics only, not a production acceptance rate.

No pinned model weights or inference runtime were found under the approved
Wrench data root, so a local SLM capability run is not yet eligible. The
candidate metadata names Qwen3.5-0.8B revision
`2fc06364715b967f1860aea9cf38778875588b17` and lists upstream bytes, but no
local shard identity has been verified. Do not infer a local route from an API
server listening on localhost. The owner has now asked for a bounded local
acceptability measurement; this supersedes this goal's earlier no-download
planning boundary only for the frozen, one-run synthetic diagnostic below.
It does not authorize training, provider traffic, OpenCode routing, or a real
workflow capture.

## Acceptance criteria

1. Freeze task classes, paired tasks, oracles, permitted inputs, and accept,
   abstain, escalation, and prohibited-action definitions before each run.
   For the first local-model diagnostic, a task class is locally acceptable
   only if every authored case in that class has an exact answer or correct
   abstention, uses the required evidence tool, cites evidence from its actual
   tool result, and has zero prohibited tool attempts or mutations. Any failed
   member leaves that class unaccepted in this diagnostic.
2. Report correct eligible accepts, correct abstentions, unresolved tasks,
   false abstentions, wrong/prohibited accepts, and escalations separately by
   class. A prohibited accept or unapproved mutation fails the safety gate.
3. Identify the exact model revision and shard hashes, inference runtime,
   tokenizer, serializer, client route, Wrench configuration, and task/source
   hashes before measuring an SLM.
4. For real-work claims, use participant-opted, repository-authorized tasks
   with per-task consent, an independent outcome oracle, and frozen splits.
   No such utility set is admitted today.
5. Compare matched tasks against a direct downstream baseline and account for
   all frontier calls, retries, verification, fallbacks, rebuilds, local
   tokens/compute, and latency. Missing usage stays unknown.
6. Keep synthetic fixture results out of utility, customer, training, and
   production aggregates.

For task `i`, report observed frontier-token savings as
`100 * (1 - W_i / B_i)`, where `B_i` and `W_i` are complete baseline and
Wrench-workflow frontier-token counts for the same task. Report the arithmetic
mean across valid paired tasks, its valid-pair count, and unresolved/excluded
counts. Separately report ratio-of-sums savings
`100 * (1 - sum(W_i) / sum(B_i))`. If either count is unavailable or the
baseline count is zero, that task's percentage is unavailable, not zero.

## Next steps

1. Freeze the model/runtime serializer identity and harden the run journal.
   The owner-requested diagnostic may download only its fully inventoried,
   revision-pinned model and hash-locked native runtime under the approved root,
   after a fresh storage reservation. Stop if package/runtime or resource
   admission cannot be reproduced.
2. Run the single preregistered, open-development challenge spanning exact retrieval, near-matches,
   changed/stale files, ambiguous requests, missing evidence, and safe
   abstention. Keep it explicitly separate from real utility evidence and
   report each class separately.
3. Only after per-task consent and outcome-oracle approval, preregister a small matched pilot
   for localization, genuine failing-test/log diagnosis, and tool/context
   selection across repositories.

No model training, download, provider request, or client prompt is authorized
by this goal.
