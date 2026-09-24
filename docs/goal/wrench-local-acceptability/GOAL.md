# Measure acceptable local work

Status: active; the first deterministic mechanics envelope is measured, while
local SLM acceptability and real-work utility remain unmeasured.

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
Wrench data root, so a local SLM capability run is not currently eligible.
The candidate metadata names Qwen3.5-0.8B revision
`2fc06364715b967f1860aea9cf38778875588b17` and lists upstream bytes, but no
local shard identity has been verified. Do not infer a local route from an API
server listening on localhost.

## Acceptance criteria

1. Freeze task classes, paired tasks, oracles, permitted inputs, and accept,
   abstain, escalation, and prohibited-action definitions before each run.
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

## Next steps

1. Select and pin an already-approved local model/runtime, or record the
   decision not to run an SLM evaluation. Before any download, use the storage
   admission and full shard/metadata inventory rules.
2. Define a local mechanics challenge spanning exact retrieval, near-matches,
   changed/stale files, ambiguous requests, missing evidence, and safe
   abstention. Keep it explicitly separate from real utility evidence.
3. Only after consent and oracle approval, preregister a small matched pilot
   for localization, genuine failing-test/log diagnosis, and tool/context
   selection across repositories.

No model training, download, provider request, or client prompt is authorized
by this goal.
