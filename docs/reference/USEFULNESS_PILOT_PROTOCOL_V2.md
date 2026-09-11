# Controlled usefulness pilot v2

Protocol status: frozen for implementation on 2026-09-10.

This protocol tests the immutable Wrench-Pro V21 package on a newly authored
Windows developer-task population. It does not reuse the V8 challenge or
release-authoring suites as an independent gate. It does not estimate general
agent quality, production traffic coverage, arbitrary shell safety, Linux or
Pi performance, or router savings outside the measured endpoint.

## Claim and population

The primary local claim is whether the V21 package produces useful, bounded
tool proposals on new supported requests. The end-to-end claim, if a complete
comparison is possible, is whether that proposal reduces work in a fixed cloud
workflow without reducing task success or crossing the execution boundary.

The frozen data directory is `data/pilots/usefulness-v2`. The evaluation split
contains 600 cases from 120 wording families, with five instances per family.
There are 60 English and 60 Chinese families, so the case split is balanced by
language. The development split contains separate families and is used only to
freeze baseline configuration and check runner behavior. The 11 contract kinds
are configuration lookup, inclusive line extraction, literal search, Git
status, latest Git subject, loopback health, review-only draft, ambiguous
selection, unsupported operation, unavailable tool, and invalid range.

The evaluation family list, prompt templates, fixture labels, and scoring code
must be frozen before model scoring. Family IDs are assigned before instances
are generated. Changing paths or identifiers does not create an independent
family. Shared tool schemas are intentional. No V8 or V21 prediction file may
be used to author or tune the evaluation.

The generated rows contain private fixture and expected-answer fields for the
executor only. The model and deterministic helper receive only `prompt` and
`context`. A public-input audit must prove that fixture contents, labels,
target calls, and private expected values are absent from that view. A separate
gold audit executes every labeled call in a disposable fixture and records any
label or environment mismatch before scoring.

## Immutable model and local limits

- Adapter package: `artifacts/model-release/package-selected-v21`.
- Adapter SHA-256: `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`.
- Package manifest SHA-256: `219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`.
- Base: `Qwen/Qwen2.5-0.5B-Instruct`, revision
  `7ae557604adf67be50417f59c2c2f167def9a775`.
- Base weight SHA-256: `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`.
- Local inference: greedy decoding, maximum 1,536 input tokens and 192 new
  tokens, with strict post-generation validation.
- All local model runs use the exact package runtime or the exact pinned base.
  A wrong package, base hash, tokenizer contract, or token limit is a hard
  preflight failure.

The base and package quality runs are direct model evaluations. They use real
disposable fixtures when `--execute` is supplied. An accepted call is useful
only when its checked fixture outcome is correct and the fixture is unchanged.

## Three-arm workflow comparison

The optional comparison uses matched task episodes:

| Arm | Workflow |
| --- | --- |
| A | Fixed cloud model chooses tools, receives observations, and answers. |
| B | Deterministic public-context helper proposes a bounded action, then the same cloud workflow verifies it. |
| C | Immutable V21 proposes a bounded action, then the same cloud workflow verifies it. |

All arms use the same system prompt, public context, tool schemas, fixture,
turn limit, and final-answer contract. Case order and arm order are randomized
with the recorded seed `20260910`. Episodes run serially. Local prediction and
validation are inside B and C clocks. Cloud calls, real tool execution,
corrections, failures, and unused proposals remain inside every episode clock.
Writes are always draft-only and never change the fixture.

Each episode allows at most three cloud turns, at most two tool calls in a
returned message, and one 45-second HTTP attempt per call. There are at most
5,400 scored attempts for 600 cases and three arms, plus a separately labeled
12-attempt development smoke allowance. The cloud client reserves the declared
maximum input and output tokens before each request, stops on budget exhaustion,
and never retries a transport failure automatically. Missing provider usage,
unexpected model identity, compound routing telemetry, or a boundary violation
stops the experiment. A partial run cannot receive a comparison verdict.

The fixed-model cloud inputs are configurable but must be explicit in
`run.json`: endpoint, requested model, observed response models, protocol,
attempt budget, token budget, body limit, seed, and timeout. The client rejects
responses whose model identity does not equal the requested model. A dynamic
router run is a different experiment and is not silently accepted as this one.

## Measures and gates

Report every assigned case, including failures and accounting failures. Local
quality reports must include:

- exact proposal accuracy and raw protocol-valid rate;
- explicit abstentions, invalid generations, and input-budget rejections;
- routine exact accuracy and checked routine outcome success;
- correct accepted routine proposals divided by all routine cases;
- incorrect accepted calls divided by accepted calls and by all requests;
- false acceptance by each negative kind;
- kind, language, and perturbation slices;
- unauthorized tool executions, filesystem changes, and complete failure rows;
- p50, p95, and p99 prediction latency, plus CUDA and process-memory receipts.

Progression gates for this authored population are raw validity at least 99.5%,
routine exact and checked outcome success at least 95%, every routine kind and
language slice at least 90%, ambiguity abstention at least 95%, zero accepted
actions on unsupported, unavailable-tool, and invalid-range cases, and zero
unexpected fixture changes. These are not production SLAs.

For the workflow, report final task success, all-episode latency, prompt,
completion, and cached tokens, actual cost when available, cloud attempts,
tool calls, correction turns, proposal errors, and unused proposals. Report
routine and negative cases separately. Usage missing from any assigned episode
is unavailable, not zero.

## Uncertainty and decision rule

The primary benefit metric is mean total cloud tokens. Mean complete episode
latency is the secondary benefit metric. Savings are `1 - mean(C) /
mean(comparator)` over all assigned episodes. A benefit interval must exclude
zero for the comparison to pass. Both C versus A and C versus B must pass.

Quality is paired by case and summarized at the wording-family level. Use
10,000 seeded bootstrap resamples of family means for descriptive intervals.
The prespecified one-sided 95% quality lower bound is the 2.5th percentile of
the paired family-difference bootstrap. If all paired differences are zero,
the bootstrap is degenerate and must not be reported as a tight guarantee. In
that case use the exact one-sided 95% lower bound for an all-success family
sample, `0.05 ** (1 / family_count)`, minus the comparator upper bound of one.
This conservative fallback is recorded explicitly and may produce
INCONCLUSIVE even when every observed episode succeeds.

The workflow result is `GO` only if both local quality and boundary gates pass,
both quality lower bounds are at least -0.02, C is no worse in observed final
success against A and B, and C saves at least 10% on the primary metric against
both comparators with intervals excluding zero. A secondary metric regression
above 10% requires a qualified decision. Any quality or boundary failure is
`NO-GO` for this candidate and workflow. Missing accounting, an unavailable
fixed control, or insufficient uncertainty is `INCONCLUSIVE`.

No result from this protocol authorizes production deployment or another
training run. A repair must be a new candidate with new development data, a
new package, and a new sealed evaluation.

## Required receipts

Each run stores a new directory and records the command arguments, checkout
commit and dirty state, protocol and source hashes, data manifest and split
hashes, model and base identity, package manifest, dependency versions,
hardware, token limits, seed, endpoint configuration, per-prediction outputs,
fixture fingerprints, raw cloud requests and responses, provider usage,
per-episode results, resource samples, analysis hash, and final report.
Local quality receipts must be generated with this protocol passed explicitly
to `scripts/release_eval.py --protocol`; the V2 analyzer binds the receipt to
the completed run's model, adapter, package, base, dataset split, and protocol
hashes. A missing or mismatched receipt is INCONCLUSIVE, while an identity-
matched failed quality gate is NO-GO.

The V2 runner must refuse an old implicit dataset or candidate. Historical V1
runs remain preserved and are never relabeled as V2.
