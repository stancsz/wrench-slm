# Goal: prove useful local selective offload for routine developer-tool work

Status: active
Updated: 2026-09-18
Owner: repository agent

## Outcome

Build a local Wrench component that can complete only a small, clearly eligible
subset of routine developer-tool work more cheaply or quickly than the stronger
model path, without reducing final task success or weakening execution controls.
Every uncertain, unsupported, risky, malformed, or failed case preserves the
original request and falls back cleanly.

The candidate path is a task-specialized sparse coding model reduced from an
officially licensed base checkpoint, if and only if the checkpoint's actual
architecture supports safe structural pruning and the resulting candidates
pass the gates below. We are evaluating three size tiers: a compact 8-expert
path near 3.9B parameters, a practical 16-expert path near 4.9B parameters,
and an expanded 32-expert path near 6.9B parameters whose ideal INT4 payload is
near 3.3 GiB. The 16-expert tier is the current more-useful quality/size
tradeoff candidate.
Deterministic rules plus cloud fallback remains an acceptable final result.

The current experimental candidate is **Wrench-Code-4B-Qwen3.6-8E**: a
3,881,244,016-parameter checkpoint pruned from Qwen3.6-35B-A3B that retains
eight experts per MoE block. `4B` is the stable parameter-class label, not a
claim about a quantized download or runtime footprint.

## Why

Routine tool selection can waste frontier-model turns and context, but a smaller
model has value only after its inference, verification, retries, corrections,
and fallback are included in the full workflow cost and latency.

## Invariants

- Wrench proposes bounded structured actions or abstains. It never owns the full
  tool loop, arbitrary shell execution, credentials, or autonomous writes.
- An independent verifier validates schema, resource identity, arguments,
  permissions, bounds, observations, and task-family rules before execution.
- Invalid, uncertain, timed-out, malformed, or boundary-changing proposals fall
  back with the original request intact.
- Rules own rigid tasks when they are as safe and useful as a learned route.
- Training data, checkpoints, raw prompts, credentials, proprietary traces, and
  customer data stay outside Git unless explicitly authorized and reviewed.
- A model's parameter count, quantization, benchmark result, or offline test
  cannot be presented as workflow value, production readiness, or token savings.

## Acceptance criteria

- [ ] Establish the candidate's exact official source, license, architecture,
  routing interface, tensor layout, and reproducible load path. Treat all
  unverified claims about a prospective model as hypotheses.
- [ ] Define a human-reviewed portfolio of low-risk, independently verifiable
  Wrench task families, exclusions, outcome verifiers, volume weights, and
  calibration/evaluation split before profiling or pruning choices are made.
- [ ] Create a reproducible router-profile receipt on the approved calibration
  corpus, including model hash, tokenizer/runtime versions, per-layer expert
  usage, routing entropy, token counts, and retained-expert selection rule for
  both candidate tiers.
- [ ] Implement structural pruning only from a verified unquantized checkpoint,
  with an architecture-aware loader, a manifest of every retained tensor, and
  load/forward parity checks. Packed quantized formats are never sliced as if
  they were ordinary floating-point tensors.
- [ ] Compare the unpruned and pruned candidates on a held-out task-family split
  with proposal correctness, prohibited accepts, abstention/fallback reasons,
  verifier outcomes, latency, memory, throughput, and calibration cost.
- [ ] If calibration is used, record its data lineage, teacher identity, budget,
  hyperparameters, held-out boundary, and before/after metrics. Do not use test
  results for tuning and then report them as final evidence.
- [ ] Produce and load-test the quantized candidate tiers: the compact
  approximately 1.8 GiB ideal-INT4 path and the practical approximately 2.3
  GiB ideal-INT4 path. Record actual packed artifact bytes, runtime identity,
  and load/forward evidence. An ideal estimate or BF16 conversion is not a
  quantized artifact. The expanded 32-expert path remains an optional BF16
  structural experiment until its packed export is justified.
- [ ] Run cloud-only, rules-plus-identical-fallback, and learned-plus-identical-
  fallback arms on the same authorized real workflow traces. The learned arm
  must show at least 10% net stronger-model-token savings versus both comparators
  with uncertainty excluding zero, no material final-success regression, zero
  prohibited accepts, and zero unexpected mutations.
- [ ] Demonstrate bounded no-mutation shadow operation: health/metrics, finite
  attempt and token ceilings, cancellation, restart/recovery, circuit breaking,
  bypass, alerting, and hash-bound rollback.
- [ ] Keep learned routing `DISABLE` until the above evidence and explicit human
  approval for an exposure-limited pilot exist.

## Non-goals

- General-purpose coding-agent replacement, anonymous weight release, public
  production claims, deployment, provider spending, or live routing enablement.
- Assuming a stated sparse-expert count, active-parameter count, VRAM fit,
  throughput, release date, or pruning outcome without inspecting the real
  checkpoint and measuring it on named hardware.

## Current approach

Start with a fact-finding and reproducibility slice: inspect the candidate
checkpoint and runtime, then design the Wrench calibration portfolio and router
profiling receipt. Do not download, rent hardware, spend provider budget, or
modify external model assets without explicit authorization.

## Current evidence

This is a clean restart. The prior implementation and all local artifacts are
preserved under
`C:\Users\stanc\github\portfolio\archives\wrench-slm-2026-09-17-pre-restart`;
none are evidence for this new candidate.

Phase 1 has now inspected the local
`Qwen3.6-35B-A3B-NVFP4` package without loading or modifying its weights. The
receipt at
`phases/phase-1-checkpoint-facts/checkpoint-facts.json` records 40 text layers,
256 routed experts, top-8 routing, 2,048 hidden size, 291 quantized modules,
and SHA-256 identities for all four `.ftw` shards (21,785,153,536 bytes total).
It also records the required stop: this packed NVFP4/FP8 artifact is not a
structural-pruning source. The next phase must obtain or identify a verified
unquantized checkpoint before any tensor slicing is attempted.

Phase 2 mechanically audited the locally staged dataset files. All 5,000 rows
parse as JSONL, but the corpus is not approved for Wrench training: the audit
shows broad web/research and finance/crypto content outside the narrow developer
tool contract. The files remain ignored and local; filtering and license/task-
family review are required before they can enter calibration or SFT.

Phase 3 identified the official unquantized Qwen source at revision
`995ad96eacd98c81ed38be0c5b274b04031597b0`. Its verified metadata declares an
Apache-2.0 model with 26 safetensor shards totaling 71,903,645,408 bytes. The
unquantized checkpoint is not present locally, so structural pruning remains
disabled pending an explicitly authorized acquisition and local inspection.

Phase 4 froze a proposed, family-disjoint portfolio in
`phases/phase-4-task-portfolio/portfolio.json`. It covers bounded reads,
literal search, read-only Git status, allowlisted local health reads, and
review-only patch drafts. Its approval status is intentionally pending human
review; the final evaluation split must not be tuned after results are seen.

Phase 5 provides a guarded acquisition command for the pinned 71.9 GB
unquantized source. It has not been run; no large download or external model
mutation has occurred.

Phase 6 found that the current global Transformers 4.57.1 cannot recognize the
Qwen3.6 `qwen3_5_moe` architecture. A project-specific runtime requirement and
non-mutating compatibility check are now recorded. Transformers 5.17.0 parses
the metadata in an isolated environment, but without PyTorch; inference status
was then verified as `READY` in a second isolated environment that reused the
existing system PyTorch. This proves runtime prerequisites only; no Qwen weights
were loaded, and GPU inference remains unverified.

The same isolated environment successfully instantiated
`Qwen3_5MoeForConditionalGeneration` on meta tensors from the local config,
without allocating weights. This closes architecture-instantiation evidence,
but not checkpoint loading, GPU execution, latency, or quality evidence.

Phase 7 exercised the local NVFP4 artifact through Docker vLLM 0.29.0. CUDA,
the RTX 5070 Ti, Qwen architecture resolution, and ModelOpt detection passed;
engine startup then failed before weight load with `UVA is not available` in the
vLLM V1 engine. No request or token was generated. The diagnostic receipt is at
`phases/phase-7-nvfp4-runtime-smoke/runtime-smoke.json`.

Phase 8 used the artifact's matching FreeToken runtime instead of the default
vLLM loader. FreeToken loaded the `.ftw` weights and expert banks with bounded
expert offload, completed CUDA-graph and prefill warmup, exposed the served
model `Qwen3.6-35B-A3B-NVFP4`, and returned the exact bounded response
`WRENCH_RUNTIME_OK` from `/v1/chat/completions`. The receipt is at
`phases/phase-8-freetoken-runtime-smoke/runtime-smoke.json`. This closes only
the local checkpoint-load and one-request runtime gate; pruning, quality,
throughput, recovery, and release gates remain open.

Phase 9 added the independent read-only execution boundary in
`src/wrench_harness/core.py`. It accepts only the versioned portfolio actions,
enforces bounded paths and reads, invokes a fixed read-only Git command,
allowlists local health endpoints, and keeps patch drafts review-only. The
boundary suite passes 4 tests, including traversal, external-health, and
automatic-application abstentions. The receipt is at
`phases/phase-9-execution-boundary/boundary-tests.json`. This proves the
verifier contract, not that the Qwen model can produce correct proposals.

Phase 10 exercised the local Qwen runtime in shadow mode. Given a strict
proposal prompt, it returned an exact `wrench.proposal.v1` read-file object;
the Phase 9 harness accepted it and observed 787 bytes without mutation. The
receipt is at `phases/phase-10-qwen-shadow-proposal/shadow-receipt.json`.
FreeToken does not support constrained JSON decoding, so schema validation and
fail-closed execution remain authoritative. This is one integration smoke
case, not a proposal-quality or workflow-success result.

Phase 11 ran the guarded preflight for the official unquantized source. The
checkpoint is absent at `D:\\models\\Qwen3.6-35B-A3B`, and the target drive has
544,558,661,632 free bytes against the 82,641,063,648-byte guard requirement.
The command refused to download without `--confirm-71gb` and created no output
directory. The preflight receipt is at
`phases/phase-11-source-acquisition-gate/preflight.json`. Structural pruning
remains disabled until that explicit operator confirmation and subsequent
official-index verification occur.

Phase 12 added `tools/validate_pruning_source.py`, a metadata-only gate that
requires the expected Qwen3.6 MoE architecture and official safetensors index
before pruning code can run. Against the real local package it returned
`eligible: false` for packed FTW shards, quantization metadata, and a missing
safetensors index. The receipt is at
`phases/phase-12-pruning-source-validator/local-validation.json`; the test
suite now passes 5 tests. No weight was loaded, sliced, or rewritten.

Phase 13 ran 10 deterministic cases from the proposed task portfolio through
the independent verifier. All 10 matched their expected accept or fallback
outcome, with zero prohibited accepts. The receipt is at
`phases/phase-13-portfolio-boundary-eval/evaluation.json`. The portfolio is
still marked `pending_human_approval`, and this boundary-only result is not
model-quality or workflow-success evidence.

Phase 14 added strict model-output parsing through
`execute_model_output`. Exact JSON objects route to the existing verifier;
markdown, prose, malformed JSON, arrays, and empty output abstain. The full
test suite passes 6 tests. The parser receipt is at
`phases/phase-14-model-output-parser/parser-tests.json`. This closes a text
boundary only and does not establish proposal quality.

Phase 15 added a bounded localhost-only adapter in
`src/wrench_harness/client.py`. It checks endpoint policy, response size,
returned model identity, and routes content through the strict parser. The
local mock-server integration suite passes 7 tests; its receipt is at
`phases/phase-15-local-qwen-adapter/adapter-tests.json`. This proves adapter
boundary behavior only, not Qwen quality or production readiness.

Phase 16 added `ProposalRouter` and `RouterConfig` for finite attempt ceilings,
circuit opening after repeated abstentions, explicit operator bypass, and
hash-bound reset. The full suite passes 8 tests. The receipt is at
`phases/phase-16-routing-guard/guard-tests.json`. Cancellation, durable
restart, alert delivery, and rollback storage remain open.

Phase 17 added schema- and configuration-hash-bound router state persistence in
`src/wrench_harness/state.py`. Save, restore, counter recovery, and
configuration-mismatch rejection pass in the 9-test suite. The receipt is at
`phases/phase-17-router-state/state-tests.json`. Process-crash simulation,
cancellation, alert delivery, and rollback storage remain open.

Phase 18 added cooperative cancellation and event hooks to the routing guard.
The 10-test suite covers cancellation, circuit-open, reset, bypass, and
observability-failure behavior. The receipt is at
`phases/phase-18-cancellation-events/control-tests.json`. Blocking-kernel
interruption and external alert delivery remain unproven.

Phase 19 exercised the real local Qwen3.6 NVFP4 runtime through the Phase 15
adapter. FreeToken served the configured model, Qwen returned a strict JSON
read proposal, and the verifier accepted the 787-byte observation without
mutation. The receipt is at
`phases/phase-19-real-qwen-adapter/runtime-receipt.json`. This proves one
real local integration path only, not model quality or workflow success.

Phase 20 measured the real adapter path with a monotonic timer. A loose prompt
abstained on invalid JSON after 4,986.808 ms; an exact-schema retry was
accepted after 1,923.364 ms with 72 prompt and 40 completion tokens. Both
attempts are preserved in `phases/phase-20-performance-smoke/performance-
receipt.json`. This is a two-attempt diagnostic, not a throughput benchmark.

Phase 21 sent five accepted-action proposal shapes from the pending portfolio
through the real local Qwen runtime, adapter, and verifier. All five were
accepted; per-case usage and wall time are recorded in
`phases/phase-21-qwen-shadow-eval/shadow-receipt.json`. This remains shadow
observation only, not calibration, final evaluation, or a quality claim.

Phase 22 acquired the explicitly authorized official unquantized source at the
pinned revision and validated its local metadata against the official
safetensors index. The checkpoint is at `D:\\models\\Qwen3.6-35B-A3B`; the
receipts are `phases/phase-22-source-inspection/checkpoint-facts.json` and
`phases/phase-22-source-inspection/pruning-source-validation.json`. The
validator reports 26 present safetensors shards, 1,045 mapped tensors, the
exact 71,903,645,408-byte index total, and `eligible: true`. This permits
profiling and pruning design, but does not establish loadability, quality,
throughput, or production value.

Phase 23 read only the safetensors headers and measured the structural expert
footprint. The source contains 35,951,822,704 BF16 tensor elements, including
33,017,561,088 routed-expert elements and 21,495,808 router elements. Keeping
8 experts per MoE block estimates 3.945B total parameters; keeping 16 estimates
4.978B. The 8-expert scenario is therefore the first measured candidate inside
the 3 to 4B target. The receipt is
`phases/phase-23-expert-size-estimate/size-estimate.json`. No expert set has
been selected, no tensor has been sliced, and no quality or runtime claim is
made.

Phase 24 streamed a provisional structural prune retaining expert indices 0
through 7 and the corresponding router rows. The resulting checkpoint,
**Wrench-Code-4B-Qwen3.6-8E**, is stored at
`D:\\models\\Wrench-Qwen3.6-8expert-BF16`, loads on CUDA, and reports
3,881,244,016 actual parameters. The receipt is
`phases/phase-24-structural-prune-baseline/prune-receipt.json`, with runtime
evidence in `runtime-smoke.json`. The result is explicitly
`EXPERIMENTAL_UNCALIBRATED`; its deterministic generation is not a quality
pass, and the selected indices are not yet Wrench-specific.

Phase 25 profiled the real NVFP4 teacher through 20 provisional Wrench prompts
across 40 routed MoE layers. The receipt is
`phases/phase-25-router-profiling/router-profile.json`; per-layer selection
receipts retain 8, 16, or 32 experts, with an aggregate fallback for the
unprofiled MTP block. Profile-informed BF16 candidates load and forward on
CUDA: they report 3,881,244,016, 4,888,532,336, and 6,903,108,976 parameters.
ModelOpt produced actual W4A16 NVFP4 exports. After removing only the unused
vision tensors for Wrench's text-only runtime, the self-contained FreeToken FTW
artifacts are 3,426,071,712 bytes for 8 experts and 3,995,579,915 bytes for
16 experts. Both report `quant_format: nvfp4` and passed bounded one-request
CUDA load/generation smokes. These remain experimental and uncalibrated, and
the 32-expert path is still BF16-only.

Phase 26 ran a development-only, fresh-wording comparison through the
independent verifier. Both final text-only FTW packs served all 10 cases, but
both scored 0/10 exact matches. Their captured outputs repeatedly looped on an
incomplete JSON fence. This is evidence that the current structural prune and
quantization preserve loadability, not Wrench behavior. The result is
explicitly provisional and does not replace the human-approved held-out gate,
teacher comparison, or calibration work.

Phase 27 added an experimental calibration path using synthetic Wrench proposal
rows, frozen pruned checkpoints, router and shared-expert gate updates, and a
small output adapter. The calibration restored valid proposal behavior on
narrow probes, but it is not a production fine-tune or a human-approved data
set.

Phase 28 reran both calibrated tiers against the same corrected 14-case
synthetic holdout. The 8-expert and 16-expert tiers each scored 9/14 in BF16
and 7/14 after NVFP4 packing. The corrected text-only FTW directories are
3,426,514,763 bytes for 8 experts and 3,996,022,974 bytes for 16 experts.
Exact proposal-object matches are 6/14 for 8E BF16, 6/14 for 8E FTW, 4/14
for 16E BF16, and 3/14 for 16E FTW. This closes the direct size comparison,
but broader held-out quality, human portfolio approval, matched workflow value,
and production enablement remain open.

Phase 29 added a separate 28-case unseen synthetic evaluation fixture. The
corrected fixture has unique IDs. The 8E packed tier scored 8/28 verifier
outcomes and 7/28 exact proposal objects; the 16E packed tier scored 9/28 and
7/28. This gives the larger tier only a small provisional edge and confirms
that neither packed tier has yet met a usefulness or release gate.

Phase 30 corrected the calibration data lineage itself: accepted byte limits
now exceed the current file sizes, and the generators write hash-stable bytes
on Windows. Fresh 500-step calibrations were quantized into new text-only FTW
packs. On the corrected 14-case holdout, 8E scored 5/14 verifier outcomes and
3/14 exact proposal objects; 16E scored 7/14 and 5/14. On the corrected
28-case unseen fixture, 8E scored 9/28 and 9/28; 16E scored 10/28 and 7/28.
The size gate is met, but usefulness, human approval, matched workflow value,
and production enablement remain open.

Phase 31 served the original Qwen3.6-35B-A3B NVFP4 teacher on the same
28-case fixture. The teacher's raw generic tool-call dialect scores 0/28 under
the strict Wrench schema, so a receipt-visible deterministic adapter was used
for semantic baseline comparison. The adapted teacher scored 12/28 verifier
outcomes and 7/28 exact proposal objects. This is a baseline, not a release
claim; the 3--4 GiB Wrench packs remain materially smaller and still require
matched workflow evidence.

Phase 32 compared the latest 8E and 16E packed tiers with that teacher on the
same 28-case fixture. Mean wall time was 6.076 seconds for 8E, 4.271 seconds
for 16E, and 9.852 seconds for the teacher. The nearest-rank p95 values were
11.275, 11.357, and 17.398 seconds respectively. This is local diagnostic
evidence only; it does not establish throughput, workflow value, or release
readiness. The receipt is `phases/phase-32-runtime-comparison/comparison.json`.

Phase 33 added an explicit action-to-field schema to the calibration prompt and
retrained both tiers without changing the verifier. The new 8E and 16E packed
artifacts are 3,423,498,137 bytes and 3,991,755,140 bytes. On the explicit
14-case holdout they scored 6/14 and 8/14 verifier outcomes, with 5/14 and
4/14 exact proposal objects. On the separate 28-case explicit-schema unseen
fixture both scored 12/28 verifier outcomes and 8/28 exact proposal objects.
The corresponding 16E BF16 holdout scored 9/14 verifier outcomes and 7/14
exact proposals before packing, making the packing loss explicit.
This is a provisional behavior improvement, not a quality or release claim.
The lineage and receipts are in
`phases/phase-33-schema-guided-calibration/comparison.json`.

Phase 34 added a receipt-only matched workflow-arm evaluator for cloud-only,
rules-plus-identical-fallback, and learned-plus-identical-fallback. It computes
paired stronger-model token savings, bootstrap uncertainty, final success,
prohibited accepts, unexpected mutations, and p95 latency. It refuses release
scoring unless the input manifest explicitly carries
`authorization: approved_real_workflow`. The placeholder manifest is recorded
as `BLOCKED_TRACE_AUTHORIZATION` in
`phases/phase-34-workflow-arm-protocol/protocol-receipt.json`; no real traces
or workflow-value claim were introduced.

Phase 35 loaded the new 8E 3.188 GiB NVFP4 pack through FreeToken and sent
diagnostic requests through the local adapter. The legacy prompt abstained on a
missing path, while the exact calibration system prompt produced one accepted,
verified bounded README read. This is one trained prompt shape only and is not
a broad quality, workflow-value, or release claim. The receipts are in
`phases/phase-35-new-tier-adapter-smoke`.

Phase 36 ran the same 28-case explicit-schema unseen fixture through the strict
local adapter for both packed tiers. The 8E and 16E tiers each accepted 10/28
responses, with 8/20 accepted task cases. Boundary safety differed: 8E had
6/8 abstentions and 2 prohibited accepts, while 16E had 7/8 abstentions and 1
prohibited accept. These are runtime development receipts only; prohibited
accepts keep both tiers non-promotable. The comparison is in
`phases/phase-36-unseen-schema-adapter/comparison.json`.

Phase 37 added all eight distinct boundary cases to a safety-focused 8E
calibration set and retrained the BF16 candidate before W4A16 NVFP4 export. The
new text-only pack remains 3,423,498,186 bytes (3.188 GiB). On the same strict
28-case unseen adapter fixture, it retained 8/20 accepted task cases and
improved boundary behavior from 6/8 abstentions with 2 prohibited accepts to
8/8 abstentions with zero prohibited accepts. This is a development safety
improvement, not workflow-value or production evidence. The comparison is in
`phases/phase-37-safety-calibration/comparison.json`.

The same safety augmentation was applied to the 16E tier. Its new text-only
pack is 3,991,755,191 bytes (3.718 GiB), with zero prohibited boundary accepts
but 6/20 accepted task cases versus 8/20 for the prior pack. It is therefore a
recorded safety candidate, not a promoted replacement for the larger tier.

The safety-calibrated 8E pack also passed a separate 14-case holdout with all
5 expected-abstention cases rejected and zero prohibited accepts, but only 4/9
task cases accepted. This confirms the safety effect without establishing
usefulness or production readiness.

Phase 38 records the dual-tier artifact selection. The safety-calibrated 8E
pack is the compact 3.188 GiB option, while the prior 16E pack is the larger
3.718 GiB option with better task acceptance than the safety-calibrated 16E
candidate. Both remain experimental and must stay behind the strict verifier,
fallback, and matched-workflow gates. The catalog is in
`phases/phase-38-dual-tier-catalog/catalog.json`.

Phase 39 tested a lighter safety-weighted 16E recalibration. The resulting
3.718 GiB pack had zero prohibited boundary accepts but only 4/20 accepted task
cases, versus 8/20 for the prior 16E pack. It is not promoted. This negative
result keeps the larger tier recommendation evidence-bounded and leaves
calibration tradeoffs open. Evidence is in
`phases/phase-39-balanced-16e/comparison.json`.

Phase 40 tested runtime prompt shaping on the prior 16E pack without changing
weights. A simple adaptive few-shot policy reached 13/20 accepted task cases,
zero prohibited boundary accepts, and 21/28 expected outcomes, versus 8/20
and one prohibited accept with the zero-shot adapter. This is diagnostic
adapter evidence only; the lexical risk classifier still needs family-disjoint
real-workflow evaluation. A separate 14-case family-disjoint holdout reached
8/14 accepted cases and 11/14 expected outcomes, but produced one prohibited
accept by turning a regex request into an accepted `literal_search` action.
This confirms the policy does not yet safely classify boundary-changing
requests. Evidence is in `phases/phase-40-few-shot-adapter/comparison.json`.

Phase 41 added a narrow request-intent guard after the Phase 40 holdout found
that regex intent could be rewritten as an accepted literal search. The guard
passes the latest user prompt into verification and fails closed with
`literal_mode_required` for that mismatch. On a rerun of the same holdout,
expected outcomes improved from 11/14 to 12/14 and prohibited accepts fell
from 1 to 0, while accepted cases were 7/14. This is still synthetic
verifier evidence only; it does not establish real-workflow value or release
readiness. Evidence is in `phases/phase-41-request-intent-guard`.

Phase 42 exercised the existing router controls across a persisted-state
boundary. Circuit opening, state save and reload, configuration-hash mismatch
rejection, hash-bound reset, and cooperative cancellation all passed in a
bounded local receipt. External alert delivery, blocking-kernel interruption,
and production rollback storage remain unproven. Evidence is in
`phases/phase-42-router-recovery/router-control-receipt.json`.
