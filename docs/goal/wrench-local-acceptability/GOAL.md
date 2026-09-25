# Measure acceptable local work

Status: active; deterministic mechanics are measured. The first local SLM
attempt was a harness failure before `model.generate`; no class is yet accepted
for a local SLM. A separately preregistered follow-up run is being prepared;
real-work utility remains unmeasured.

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

The pinned Qwen3.5-0.8B revision
`2fc06364715b967f1860aea9cf38778875588b17` is now stored under the approved
Wrench data root with all 13 files hash-verified. The Windows CPython 3.13.15
runtime is pinned and installed, and the exact 35-package lock, CUDA 13.2,
and RTX 5060 Ti capability are verified. Do not infer a local route from an
API server listening on localhost. The owner's request authorizes only the
bounded synthetic local measurement described here. It does not authorize
training, provider traffic, OpenCode routing, or a real workflow capture.

The first pinned runtime/model load completed within the resource reserve, but
run 01 failed before the model call: `apply_chat_template` returned a
`BatchEncoding`, and the runner attempted to parse the object key as a token.
The durable failure report is
`C:\wrench-slm-data\artifacts\wrench-local-acceptability\qwen35-0.8b-synthetic-20260925-01.json`.
It has zero generated tokens, zero completed cases, one failed case, and nine
not-run cases. It is harness evidence, not model-quality evidence. In response
to the owner's current request to begin measuring, this goal preregisters one
separate follow-up run after the serializer fix. It has a fresh output receipt
and admission check; errors will stop it without retrying.

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

1. Keep run 01 as harness-invalid. Normalize the pinned tokenizer's
   `BatchEncoding["input_ids"]` before counting or device transfer, and retain
   bounded exception details for any later runtime failure. Tokenizer-only
   preflight now yields a tensor of shape `(1, 270)` for the first frozen case;
   no model generation was used for that check.
2. Run one separately preregistered follow-up challenge spanning exact
   retrieval, near-matches, changed/stale files, ambiguous requests, missing
   evidence, and safe abstention. Keep run 01 as a failed harness receipt,
   keep run 02 separate from real utility evidence, and report each class.
3. Only after per-task consent and outcome-oracle approval, preregister a small matched pilot
   for localization, genuine failing-test/log diagnosis, and tool/context
   selection across repositories.

No model training, provider request, OpenCode routing, client prompt, or real
workflow capture is authorized by this goal. The existing model/runtime
download is complete. The follow-up authorizes one local synthetic inference
run only; any retry or broader diagnostic requires a new preregistration.
