# Measure acceptable local work

Status: active; the deterministic proposal route passed a 176-case synthetic
development screen across six bounded action families. Open-fixture
route-to-executor screens cover exact file reads, line-range reads and literal
searches with evidence-bound abstentions. A fresh patch-operation screen
matched 12/12 exact draft oracles across replacement, append, insert-after,
and explicit whole-line removal, plus 9/9 abstention boundaries. These are
draft mechanics only. The first local SLM screen failed all five classes.
The fresh 18-case prompt-only screen also passed no generative task class:
0/12 answerable cases met the exact answer/schema/evidence oracle, while 3/6
boundary examples were correctly abstained. Training remains stopped pending
a held-out, tool-backed outcome screen. Real-work utility and frontier-token
savings remain unmeasured.

## Objective

Establish which bounded coding-agent tasks Wrench can safely complete locally,
which it should abstain from, and which must be escalated. Measure task quality
and frontier-token effects on matched work before training or promoting a
learned controller.

## Current decision

The current scope decision is recorded in the [local task acceptance
envelope](../../reports/wrench-local-acceptability/local-acceptance-envelope-20260925.md):
exact snapshot file reads, line-range reads, and literal searches have
mechanics evidence only; Git status, health reads, and open-ended or multi-file
patch drafts have proposal evidence only; and no semantic local SLM class is
accepted. The fresh patch-operation screen matched 12/12 exact diffs and
independent target applications, with 9/9 boundaries abstaining and fixture
trees unchanged. It covers only exact replacement, append with a final LF,
insertion after a unique single-line anchor, and explicitly requested
whole-line removal on small UTF-8 LF files. It establishes review-draft
mechanics, not semantic repair correctness, open-ended patching, or completed
coding work. See the [operations screen report](../../reports/wrench-local-acceptability/patch-operations-screen-01.md)
and [evaluation](../../evals/wrench-local-acceptability/patch-operations-screen-01-result.md).
The first fresh-fixture route-to-verifier screen for generic review-only patch drafts
failed its exact positive-oracle rule (1/3), although all three boundaries
abstained and all fixture trees stayed unchanged. See the [screen report](../../reports/wrench-local-acceptability/patch-draft-screen-01.md).
The identified parser defects passed 33 focused tests after repair, but that
generic screen was not repeated, so its generic patch scope remains
unaccepted. See the
[repair follow-up](../../reports/wrench-local-acceptability/patch-draft-screen-01-followup.md).
The follow-up [screen 02](../../reports/wrench-local-acceptability/patch-draft-screen-02.md)
matched 3/4 positive drafts and all six boundaries; its remove-setting result
failed the exact target oracle. The earlier [whole-line removal screen](../../reports/wrench-local-acceptability/patch-whole-line-screen-01.md)
passed 3/3 explicit line removals and 6/6 boundaries. The later operations
screen covers three fresh cases per supported operation.
The M3 tokenizer proxy is secondary because prompt size cannot decide task
acceptability. Training stays stopped until a preregistered, held-out task
class passes its outcome and safety criteria.

The first frozen M3 context-token screen measured five of seven positive
evidence selections and all four abstention boundaries. Five eligible cases
reduced complete input tokens by an 11.64% arithmetic mean and 12.11% by
ratio-of-sums. The two function-location cases failed the required answer
evidence check, so the screen acceptance is FAIL and those pairs are excluded.
The accepted rows cover only exposed synthetic log triage, exhaustive literal
search, and exact config reads. No model ran, and frontier-token savings remain
N/A. See the [screen result](../../evals/wrench-local-acceptability/synthetic-context-token-reduction-screen-01.md)
and [frozen protocol](../../evals/wrench-local-acceptability/synthetic-context-token-reduction-protocol-06.md).

The current provider-free rule route has a narrow measured operation envelope:
bounded exact file reads, line-range reads and literal searches on an explicit
supplied snapshot, with correct abstention on the measured missing, stale,
out-of-range and ambiguous evidence cases. These are retrieval and observation
mechanics, not semantic answer generation or natural-language coding-task
completion. They do not establish general code editing, root-cause diagnosis,
real-repository utility or local SLM capability. The latest [line-range
screen](../../reports/wrench-local-acceptability/local-read-lines-acceptability-03.md)
passed 6/6 routes, 2/2 exact executor observations and 4/4 abstentions on its
exposed six-case fixture; independent receipt review passed.

A broader deterministic proposal-route screen now covers `read_file`,
`read_lines`, `literal_search`, `git_read_status`, `health_read`, and
review-only `patch_draft`. On 96 eligible and 80 boundary/out-of-domain
calibration/development cases, it matched all 96 frozen proposal targets and
made zero unsafe proposals. The detailed [measurement report](../../reports/wrench-local-acceptability/local-work-envelope-20260924-01.md)
shows the per-family counts and limitations. This is a route mechanics result:
no actions or verifier were run, and the synthetic cases are exposed. It does
not establish complete task success or real-work acceptability.

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

The separate [prompt-only local work screen](../../reports/wrench-local-acceptability/prompt-only-local-work-screen-01.md)
completed all 18 synthetic generations. It accepted no positive answer under
the frozen exact oracle, passed only three correct abstentions, and failed all
three classes. Log mapping cited source lines but returned exception names
instead of normalized categories; config responses often violated the exact
JSON schema; localization omitted the property-access evidence and guessed on
boundaries. These results nominate no semantic work for LoRA training. Keep
the outputs untrusted and do not tune on this exposed fixture. This separate
prompt-only diagnostic has no tool result, held-out split, real-task oracle,
or frontier usage, so it does not meet the goal's local SLM gate and provides
no token-savings number. See the [result evaluation](../../evals/wrench-local-acceptability/prompt-only-local-work-screen-01-result.md)
and [frozen protocol](../../evals/wrench-local-acceptability/prompt-only-local-work-screen-01-protocol.md).

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

The corrected synthetic run 02 completed all ten model responses at the pinned
identities. It made zero required read-tool calls, scored every class 0/2, and
had no safety-counter violations. It produced two unsupported `known` claims
and eight `unknown` responses, including five false abstentions on answerable
cases. Strict correct abstentions and grounded accepts were both 0/10. This
does not meet the local-acceptability rule for any measured class. The exact
receipt, counts, latency, and scope limits are in the [run 02 report](../../reports/wrench-local-acceptability/local-slm-run-02.md).

The [corrected deterministic operation screen](../../reports/wrench-local-acceptability/local-exec-acceptability-02.md)
joined the snapshot-bound E0 route to the independent bounded core executor
on the same ten admitted synthetic cases. Exact route outcomes were 10/10;
the executor returned 7/7 exact read/search observations; E0 made 3/3 correct
missing/stale/ambiguous abstentions. All five fixture pairs passed their
operation screen, with zero false abstentions or mutations. The initial
attempt is preserved as [scorer-invalid](../../reports/wrench-local-acceptability/local-exec-acceptability-01.md).
Both runs are open-development mechanics only; the read/search prompts are
explicit operations and do not evaluate the separate semantic answer oracle.

The existing [paired frontier-savings reporter](../../../tools/report_paired_frontier_savings.py)
validates complete matched outcome receipts and computes both the arithmetic
mean of per-task savings and the ratio-of-sums. It now also emits per-task
counts, percentage, or exclusion reason, keyed by a hashed task reference.
There are still zero eligible matched frontier-usage pairs. Run 02's local
tokens and the deterministic seed's 10/10 fixture result do not enter this
metric. The exact evidence and remaining permission/runtime gates are in the
[frontier measurement readiness review](../../evals/wrench-local-acceptability/frontier-token-readiness.md).

A receipt-only join of the existing failing-log pair further separates the
local operation from task completion: deterministic exact log retrieval passed
2/2 cases, while the Qwen SLM made 0/2 required tool calls and completed 0/2
triage outcomes. The source fixture was exposed, and the operation arm asked
for an exact read rather than the SLM's semantic classification, so this is a
diagnostic, not a matched-prompt or held-out result. It accepts only the
retrieval mechanics; semantic local SLM acceptance remains at zero classes.
See the [triage-stage diagnostic](../../reports/wrench-local-acceptability/local-triage-stage-diagnostic-20260925.md)
and [evaluation](../../evals/wrench-local-acceptability/local-triage-stage-diagnostic-20260925.md).

An offline [attempt-ledger bridge](../../reports/wrench-local-acceptability/frontier-attempt-ledger-bridge.md)
now adapts complete, caller-supplied frontier-only ledgers into the reporter's
existing receipt format. It requires exact token counts, known cost for every
frontier call, and explicit zero local-model, tool, and verifier calls; it
rejects mixed routes, fallbacks, unrun attempts, and unknown outcomes. CLI
stdout stays reporter-compatible, with detailed arm exclusions on stderr.
Eleven standard-library fixture checks pass. This only verifies conversion and
exclusion mechanics. It is not valid for Wrench SLM or mixed workflows, does
not authenticate telemetry, and adds no observed savings pair. Average
frontier savings remain N/A with zero eligible pairs.

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

1. Keep the first route-to-executor attempt scorer-invalid and its corrected
   ten-case run as exposed mechanics-only evidence. Keep line-range screen 03
   as a separate six-case mechanics result, the 176-case route screen as
   proposal-only, and Qwen run 02 as a failed synthetic SLM screen. Do not tune
   against or train on these exposed fixtures.
2. Use the paired receipt reporter for a savings figure only when both arms
   have complete exact usage receipts for the same tasks, source snapshots,
   preregistered arm definitions, downstream route and token convention. The
   reporter validates declared identities; it does not prove prompt/information
   parity or authenticate traces. The current result is N/A, with zero valid
   pairs. The route through localhost:4000 is a mutable gateway route to
   OpenRouter/MiniMax, not a pinned local model or a verified client/tokenizer
   pair.
3. Before provider-backed measurement, obtain the separate authority required
   by `COLLABORATION_CONTRACT.json` for provider usage/spend. For real-work
   claims, also approve participant/task consent, source authorization,
   capture/retention/deletion terms and an independent outcome oracle. Then
   freeze the client, model/route, accounting convention, protocol, and task
   split before any calls. The [pilot-readiness goal](../wrench-northstar-pilot-readiness/GOAL.md)
   holds the owner decisions and study design.

4. Keep the patch-operation screen result scoped to the four explicit
   single-file draft forms and synthetic UTF-8 LF inputs. Open-ended,
   multi-file, semantic repair and completed coding claims remain outside it.
5. Diagnose why the two exposed function-location cases failed the required
   answer-evidence check. Do not tune on those exposed fixtures. Then
   preregister a fresh, independent localization fixture with source-derived
   required-path and quote oracles, missing/stale/ambiguous boundaries, and an
   over-budget boundary. Count a case complete only when exact evidence is
   present and all abstentions match; report token reductions only for eligible
   cases and keep semantic SLM acceptance separate.

No additional model training, provider request, OpenCode routing, client
prompt, or real workflow capture is authorized by this goal. The local
proposal and synthetic operation-path measurements are complete at their
limited scopes. Natural-language task completion, held-out generalization,
and real-work utility remain unmeasured; they need an independently reviewed
outcome oracle and, for real-work claims, consented authorized tasks.
Keep training stopped: the local SLM has zero accepted task classes.
Provider-backed savings still have zero eligible matched usage pairs and need
the separate authority described above.
