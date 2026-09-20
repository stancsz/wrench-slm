# Goal: Wrench 多快好省

Status: active
Updated: 2026-09-20
Owner: repository agent

## Outcome

Deliver one smallest-sufficient Wrench SLM that makes routine, mechanically
verifiable developer-tool work **多快好省** when combined with the stronger
frontier model:

- **多**: correctly cover at least 90% of the weighted mechanical-workload
  frontier-token mass without a frontier fallback, measured on authorized
  representative traces rather than synthetic case count alone.
- **快**: materially reduce successful eligible-task end-to-end latency, with
  median and p95 measured against the same teacher-only workflow.
- **好**: preserve final task success, use the independent verifier, produce
  zero prohibited accepts and zero unexpected mutations, and abstain cleanly
  whenever the task is uncertain or outside the approved portfolio.
- **省**: deliver at least 95% net frontier-token savings versus teacher-only,
  after fallback, retries, corrections, verifier work, and context compaction
  are included.
- **Teacher parity**: on the authorized mechanical-work portfolio, the
  `wrench_plus_identical_minimax_fallback` arm has no material final-success or
  verifier-success regression versus the MiniMax teacher-only arm.

Expert count, parameter count, pruning ratio, quantization, and adapter type
are implementation variables. Choose the smallest candidate that passes the
workflow gates. The historical 8E and 16E artifacts remain comparison
evidence, not product tiers. The previous 4.25B figure remains a ceiling for a
candidate unless the product owner explicitly changes it, not the North Star
and not a reason to keep a larger model.

Every uncertain, unsupported, risky, malformed, or failed case preserves the
original request and falls back cleanly. Rules may own rigid tasks when they
are safer and more economical, but the complete Wrench-plus-fallback workflow
must be measured against teacher-only.

Here "original full weights" means the existing Desktop
Qwen3.6-35B-A3B-NVFP4 package with all routed experts retained. It is quantized,
not the original BF16 precision checkpoint. Record both identities explicitly
if a BF16 comparison is added. Independent execution verification remains
required regardless of model size.

## North Star measurement contract

The primary release decision is made on a frozen, human-reviewed, redacted
workflow trace set with production task-family weights. The canonical 220-case
suite is a semantic and safety regression gate, not a substitute for the
weighted workflow measurement.

Define the three arms on identical traces:

1. MiniMax teacher-only;
2. rules plus identical MiniMax fallback;
3. Wrench plus identical MiniMax fallback;
4. Wrench-only diagnostic.

Report separately and together: verified mechanical coverage by task volume and
frontier-token mass, final success, correct acceptance, abstention, fallback,
retry, correction, local Wrench tokens, frontier tokens, total tokens, cost,
latency, prohibited accepts, and unexpected mutations. A lower teacher-call
count or a smaller checkpoint alone is not savings evidence.

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
- The RTX 5070 Ti workstation and 5060 Ti worker use the same hash-identified
  source commit, artifact commit, tokenizer, runtime, verifier, and manifest
  when they are evaluating the same candidate. The 5070 Ti owns interactive
  development and same-host comparison; the 5060 Ti owns independently
  reproducible batch evaluation and artifact re-verification. Host-specific
  latency and memory results remain separate and are never merged into a
  same-hardware claim.

## Acceptance criteria

- [ ] Deliver one hash-identified smallest-sufficient standard Wrench model
  artifact with a Hugging Face-compatible Safetensors package, tokenizer,
  context policy, and verified load/generation path. FreeToken remains a
  comparison backend, not the canonical serving artifact. The current
  4,250,000,000-parameter figure is an implementation guard only; expert count
  and parameter count do not decide success.
- [ ] Measure candidate selection by the North Star gates, not by expert count:
  verified mechanical coverage, final success, safety, frontier-token savings,
  total cost, and end-to-end latency.
- [ ] Reproduce the selected candidate across the RTX 5070 Ti and 5060 Ti
  worker using the same source commit, artifact commit, manifest hashes,
  tokenizer, runtime, verifier, prompts, and decoding contract. Record
  host-specific load, memory, latency, throughput, retry, and failure receipts;
  use the 5060 Ti for independent batch verification without treating its
  different hardware as a same-host speed comparison.
- [ ] Freeze the MiniMax-worker trace set, family-disjoint splits, workload
  weights, labels, teacher identity receipt, and scoring code before candidate
  selection. The new contract must include routine mechanical work, recent
  context, old-lookup retrieval, irrelevant-history pressure, boundary and
  injection cases, complex fallback, and 2M-payload stress. Existing 28-case
  and 220-case fixtures are regression evidence only. No final trace or answer
  may enter training, expert selection, or prompt tuning.
- [ ] On a fresh family-disjoint semantic test set, report eligible-task
  correct acceptance, overall expected-outcome match, exact abstention reasons,
  malformed outputs, service failures, prohibited accepts, and paired
  confidence intervals. The model need not win an academic score if the
  complete measured workflow passes the North Star gates, but it may not trade
  away safety or final task success to obtain token savings.
- [ ] Measure high-throughput serving on the same matched traces, with at least
  three repetitions after readiness/warmup. Report successful-task p50/p95
  prefill, decode, end-to-end latency, throughput, cache hit rate, peak memory,
  and cold-load time separately. Quick refusals cannot masquerade as fast
  mechanical completion.
- [ ] Compare exact request payloads, prompts, decoding parameters, token caps,
  verifier, task starting state, and retry policy on the same hardware/runtime.
  Separate cold and warm cache runs. Terminate and verify exit of all owned
  worker processes between arms, record free VRAM and background load, and
  counterbalance arm order. Preserve raw outputs and every failed attempt.
  Differences in tokenizer, quantization, or cache allocation must be reported.
  Require zero prohibited accepts and zero unexpected mutations on the suite;
  do not relax the verifier to improve acceptance. Benchmark gains alone do
  not satisfy the production-value gates below.
- [ ] Establish the candidate's exact official source, license, architecture,
  routing interface, tensor layout, and reproducible load path. Treat all
  unverified claims about a prospective model as hypotheses.
- [ ] Define a human-reviewed portfolio of low-risk, independently verifiable
  Wrench task families, exclusions, outcome verifiers, volume weights, and
  calibration/evaluation split before profiling or pruning choices are made.
- [ ] Create a reproducible router-profile receipt on the approved calibration
  corpus, including model hash, tokenizer/runtime versions, per-layer expert
  usage, routing entropy, token counts, and retained-expert selection rule for
  the single selected candidate and its comparison references.
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
- [ ] Produce and load-test the single selected quantized candidate. Record
  actual packed bytes, runtime identity, and load/forward evidence. Ideal INT4
  estimates are not artifact sizes. Additional size tiers are comparison
  artifacts only unless the smallest-sufficient candidate changes.
- [ ] Run MiniMax teacher-only, rules-plus-identical-fallback, and
  Wrench-plus-identical-fallback arms on the same authorized teacher traces.
  The Wrench arm must cover at least 90% of weighted mechanical frontier-token
  mass, preserve teacher final success within the frozen non-inferiority margin,
  and show at least 95% net frontier-token savings versus teacher-only, with
  paired uncertainty, zero prohibited accepts, zero unexpected mutations, and
  separately reported local inference overhead.
- [ ] Accept up to 4,000,000 tokens directly at the Wrench model serving
  endpoint, like an Ollama model with `num_ctx=4000000`. The receipt must bind
  tokenizer identity, configured max context, actual model-side prompt tokens,
  and no-truncation evidence. A gateway, AST, context ledger, summary, or
  preselector may optimize cache and retrieval, but cannot replace the native
  direct-input gate. Keep recent hot/warm context active by default, keep old
  lookups reference-only, and produce a hash-bound selection receipt for every
  optional omitted or retrieved span. Measure serving at 64K, 128K, 256K, 2M,
  and the 4M stress point where hardware permits.
- [ ] Keep 2,000,000 direct model input as an intermediate milestone. A 2M pass
  is useful evidence, but it does not close the 4M target or authorize release.
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

Capture and approve MiniMax teacher traces first. Rebuild the evaluation around
weighted mechanical frontier-token mass, teacher parity, recent-context
behavior, reference-only old lookups, native direct 2M model input, and matched
fallback accounting. Use those traces to teach and select Wrench, while keeping
the final family-disjoint split sealed. Then produce one standard Safetensors
artifact and validate direct vLLM serving first, with Ollama compatibility
measured separately.
LoRA, pruning, quantization, expert count, and runtime cache strategy are
implementation variables. None may be optimized against the sealed final set.

This revision records the user's single-model experimental objective. It does
not declare the performance targets feasible or achieved. Keep source artifacts
recoverable. Provider spending, external data use, publication, and production
enablement retain their existing authorization boundaries.

The current worker split is deliberate: the RTX 5070 Ti remains the interactive
builder and same-hardware comparison host, while the 5060 Ti is an asynchronous
batch worker for independent evaluation, artifact integrity checks, and
repeatable long-running jobs. Code and instructions synchronize through the
source repository. Large checkpoints synchronize through the private Git LFS
artifact repository. Job manifests, heartbeats, logs, and result receipts use
the approved worker exchange channel. A worker must not silently substitute a
different checkpoint or runtime.

## Remaining gap for the revised objective

No candidate has passed the new North Star contract. Phase 58 contains exploratory results
on a repeatedly used fixture, with different initial free VRAM across arms and
unverified worker-process cleanup. Its latency ratio is not a controlled speed
claim. A fresh independent comparison and a single selected smallest-sufficient artifact remain
required. Cross-host synchronization is documented, but a 5060 Ti fetch and
host-labeled verification receipt for the selected candidate are not yet
visible. Historical multi-tier notes below are provenance, not current scope.

## Human authorization record

On 2026-09-19, the product owner authorized the repository agent to take the
bounded actions needed to pursue the remaining release-quality evidence,
including approved live evaluation work, provider-backed workflow traces, and
reversible local implementation and verification. This authorization does not
change product intent, acceptance criteria, hardware boundaries, data lineage
rules, or commit authority. It does not convert missing evidence into a pass,
authorize production routing, deployment, publication, or release, and it does
not permit weakening any safety or verifier gate. The product owner
confirmed that the release target is one smallest-sufficient standard model
artifact that behaves like a specialized MiniMax worker on the mechanical
portfolio, accepts a direct 4M model input through standard serving, and is selected by the
revised teacher-parity contract. The historical 4.25B figure is an
implementation guard, not the product objective. Learned routing remains
`DISABLE` until every acceptance criterion passes and final human release
approval is separately recorded.

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

Phase 43 re-verified the live quantized artifacts and their manifests. The
compact 8E safety tier remains 3.188 GiB on disk with 3.169 GiB of packed
weights and 3,881,244,016 parameters. The larger 16E tier remains 3.718 GiB
on disk with 3.697 GiB of packed weights and 4,888,532,336 parameters. Both
still pass the export and text-only receipts, while the catalog continues to
make no quality or production claim. Evidence is in
`phases/phase-43-artifact-reverification/catalog.json`.

Phase 44 attempted to rerun the compact 8E adaptive holdout, but the available
FreeToken environment could not be restored: the shell interpreter lacked the
package and CUDA-enabled PyTorch, and the editable build stopped because
`CUDA_HOME` was unset. No weights were loaded and no request was served. This
is a runtime-prerequisite diagnostic, not a model-quality result. Evidence is
in `phases/phase-44-compact-runtime-prerequisite/diagnostic.json`.

Phase 45 restored the CUDA FreeToken environment and evaluated the compact 8E
artifact on the same 14-case adaptive holdout as the larger tier. Before the
destructive-intent guard it accepted 4/14 cases, matched 7/14 outcomes, and
had 1 prohibited accept. After the guard it accepted 3/14, matched 8/14, and
had 0 prohibited accepts. The larger 16E reference remains stronger on this
holdout at 7/14 accepted and 12/14 expected outcomes with zero prohibited
accepts. This is synthetic runtime evidence only. Evidence is in
`phases/phase-45-compact-holdout/comparison.json`.

Phase 46 reran the larger 16E artifact after the destructive-intent guard. On
the same 14-case holdout it remained at 7/14 accepted, 12/14 expected
outcomes, and zero prohibited accepts. Directly compared with the compact 8E
result of 3/14 accepted and 8/14 expected outcomes, the larger tier is the
more useful experimental candidate while both remain behind fallback and real
workflow gates. Evidence is in
`phases/phase-46-larger-holdout/comparison.json`.

Phase 47 summarized runtime and reported-token accounting from the paired
guarded holdout. The 8E tier was faster at 25.390 seconds total, 1,813.6 ms
mean, and 2,380.6 ms p95, with 4,542 reported tokens. The 16E tier took
30.621 seconds total, 2,187.2 ms mean, and 3,262.0 ms p95, with 4,590
reported tokens, while delivering the stronger acceptance result. This is
local synthetic diagnostic evidence, not paid-token savings or production
latency proof. Evidence is in
`phases/phase-47-guarded-runtime-cost/comparison.json`.

Phase 48 ran the broader 28-case explicit-schema fixture through both guarded
tiers. The 16E tier accepted 14/28, matched 22/28 outcomes, and had zero
prohibited accepts. The 8E tier moved from 12/28 accepted and one prohibited
traversal rewrite to 11/28 accepted, 19/28 matches, and zero prohibited
accepts after the traversal guard. This confirms the larger tier is the more
useful experimental candidate, while the compact tier remains the faster,
smaller safety option. Evidence is in
`phases/phase-48-guarded-unseen/comparison.json`.

Phase 49 performed a requirement-level audit against every acceptance criterion
in this file. The result is `NO_GO_EXPERIMENTAL_ONLY`: the 3–4 GiB quantized
tiers, synthetic quality comparisons, and local bounded controls are evidenced,
but human portfolio approval, authorized real workflow traces, external alert
delivery, and production enablement remain open. The audit is recorded in
`phases/phase-49-release-gate-audit/audit.json`.

Phase 50 made the rollout hold explicit in
`config/wrench-routing-policy.json`: learned routing is `DISABLE`, and the
stronger-model fallback remains authoritative until the listed evidence and
human pilot approval exist. The policy is covered by a regression test in
`tests/test_policy.py`.

Phase 51 tightened the real-workflow protocol. An approved trace manifest now
requires a trace-set SHA-256 plus capture ID, timestamp, reviewer, and source
scope before paired savings are computed. Missing provenance is explicitly
blocked, and no real trace data was added. Evidence is in
`phases/phase-51-trace-provenance-gate`.

Phase 52 made the trace authorization receipt hash-integrity checked. For an
approved manifest, the evaluator recomputes the canonical trace-set SHA-256
and blocks any mismatch before calculating paired savings. No real workflow
data was added. Evidence is in `phases/phase-52-trace-hash-integrity`.

Phase 54 separated ideal INT4 payload estimates from actual NVFP4 artifacts.
The ideal half-byte estimates are 1.808 GiB for 8E and 2.277 GiB for 16E,
while verified packed weights are 3.169 GiB and 3.697 GiB, with full text-only
directories at 3.188 GiB and 3.718 GiB. The practical 3–4 GiB artifact target
is met; the ideal estimates are not download-size claims. Evidence is in
`phases/phase-54-ideal-vs-packed-size/comparison.json`.

Phase 55 added the current tier-selection guide at
`docs/WRENCH_MODEL_TIERS.md`. It makes the 8E compact and 16E larger artifacts
usable as explicit experimental choices while preserving the strict verifier,
stronger-model fallback, and disabled learned-routing policy.

Phase 56 added a fail-closed tier resolver in `src/wrench_harness/tier.py`.
It selects only the verified compact or larger catalog entry, requires the
learned-routing policy to remain `DISABLE`, rejects missing artifacts, and
labels every result `EXPERIMENTAL_ONLY`.

Phase 57 verified that resolver against the live Phase 43 catalog, routing
policy, and both external quantized artifact directories. Both compact and
larger selections resolved as `EXPERIMENTAL_ONLY` with learned routing
`DISABLE`. Evidence is in
`phases/phase-57-live-tier-resolution/live-tier-resolver-receipt.json`.

Phase 59 expanded the evaluation boundary to 220 deterministic cases across
the six approved task families plus 40 explicit out-of-domain negatives:
120 eligible workflow proposals, 60 boundary or failure cases, and 40
unrelated-task abstention cases covering React work, database migration, shell
execution, Git publication, authentication redesign, multi-step debugging,
deployment, general coding, external API integration, and destructive file
operations. The suite is balanced at 30 in-domain cases per family, with
out-of-domain cases kept in their own category, and split into 132
calibration, 44 development, and 44 draft final cases. Template groups remain
confined to one split. The canonical grouped suite and hashes are in
`evals/wrench-expanded-v1/manifest.json`, and offline manifest plus verifier
validation passed in `evals/wrench-expanded-v1/validation.json`.
This is a coverage expansion marked `DRAFT_PENDING_HUMAN_APPROVAL`; it is not
yet final quality evidence, and accepted health-read cases still require live
endpoint execution receipts. The out-of-domain guard returns the stable
`task_family_not_allowlisted` reason even when a prompt contains a safe-looking
proposal.

Phase 60 added `tools/run_workflow_arm_replay.py`, a receipt-only assembler for
matched `cloud_only`, `rules_plus_identical_fallback`, and
`learned_plus_identical_fallback` traces. It records final success,
prohibited accepts, unexpected mutations, stronger-model and total tokens,
retry count, provider requests, cost, and latency, then delegates paired
token/cost and latency scoring to the Phase 34 evaluator. It requires matched
IDs, canonical trace hashing, provenance, and explicit
`approved_real_workflow` authorization before opening the quality gates. It
does not call providers, spend money, execute proposals, or authorize
production enablement; no real replay traces are claimed by this phase.

2026-09-19 Builder verification: the product owner explicitly approved
advancing the evaluation work within this contract. Re-ran the expanded-suite
validator and focused replay/schema tests: `PASS_EXPANDED_EVALUATION_MANIFEST`
for 220 cases (120 eligible, 60 boundary, 40 out-of-domain; 132 calibration,
44 development, 44 draft-final; 20 live executions skipped) and `8 passed`.
This verifies manifest and harness integrity only. The final slice remains
non-authoritative until the approved human labels and live health receipts are
captured, and no real workflow replay or release-quality claim is introduced.

2026-09-19 one-expert sizing: measured the verified unquantized source from
safetensors headers only for exactly one retained expert per MoE block. The
estimate is 3,041,824,624 parameters across 40 layers and 41 MoE blocks, with
32,909,998,080 routed elements removed from the 256-expert source. This is a
structural estimate only; no expert was selected, tensor payload was loaded, or
quality claim was made. Receipt: `phases/phase-61-one-expert-size/size-estimate.json`.

2026-09-19 one-expert selection tooling: extended the router-selection and
structural-pruning tools to support an explicit target top-1 router while
retaining one telemetry-ranked expert per route. Derived the 40-route,
one-expert selection receipt from the existing router telemetry and compiled
both tools successfully. Receipt:
`phases/phase-61-one-expert-size/selection-1.json`. The checkpoint has not yet
been written or load-tested.

2026-09-19 full 220-case 8E evaluation: ran the canonical
`evals/wrench-expanded-v1/cases.jsonl` suite end to end against
`Wrench-Code-4B-Qwen3.6-8E-Safety-Experimental`. All 220 requests completed,
all 220 case IDs were unique, and there were zero transport failures. The
receipt reports 30/120 eligible exact proposal matches, 20/60 boundary correct
outcomes, 40/40 out-of-domain correct abstentions, 90/220 overall correct
outcomes, and 15 prohibited accepts. The 20 eligible health-read cases were
not live-service evidence because no allowlisted health service was included
in the run. Receipt and detailed breakdown:
`phases/phase-62-full-220-evaluation/receipt-8e.json` and
`phases/phase-62-full-220-evaluation/README.md`. This is a completed full-suite
diagnostic run and is not a release pass.

2026-09-19 mechanical long-context serving: changed the default staged working
context from 40K to 64K, with a 48K recent hot budget and a 16K mechanical
reference-card budget. Integrated the reducer into the local FreeToken Wrench
serving submission path. A real 4M-configured endpoint accepted a raw input
estimate of 4,000,023 tokens and produced an exact 1,278-token model prefill;
the reducer reported 123.772 ms cold ingestion and 0.245 ms hot selection.
This is runtime integration evidence only. Native 4M attention, retrieval
recall, worker quality, and production release gates remain open.

2026-09-19 native retrieval and portable package evidence: the deterministic
220-case mechanical retrieval diagnostic passed with 1.0 target-reference
recall, 1.0 current-intent preservation, and 1.0 hash-bound reference rate;
receipt: `phases/phase-71-native-retrieval-quality/retrieval-220.json`. The
reducer-bypassed native 1M probe on the 4M-configured endpoint was stopped
after 567 seconds without an HTTP response while GPU work remained saturated;
receipt: `phases/phase-71-native-retrieval-quality/native-1m.json`. Native 1M
and 2M attention are therefore not release claims. A portable package now
bundles the custom tokenizer hook and mechanical prefill dependency so a local
Transformers loader can stage long input without a separately installed
harness. Structural validation passes. At the user's explicit request, the
package is now a public experimental artifact at
`stancsz/Wrench-4B-Qwen3.6-8E`; this does not authorize production claims.

2026-09-19 mechanical fast path and calibration evidence: added a conservative
deterministic parser for high-confidence read_file, read_lines,
literal_search, git_read_status, and explicitly bounded health requests. Its
proposals still pass the existing verifier and multi-pass TTC guard; malformed
or risky requests fail closed. On the historical 220-case diagnostic replay,
the original v7 Safety model plus this fast path produced 156/220 correct
outcomes, 80/120 exact eligible accepts, zero prohibited accepts, zero
transport failures, and 137 mechanical fast-path requests. This is not the
final matched MiniMax workflow score. The parser and runtime are also bundled
into the portable package and verified through `AutoTokenizer` dynamic-module
loading. A LoRA/router calibration probe was measured and rejected after it
produced 86/220 correct outcomes and 24 prohibited accepts.

2026-09-19 teacher-aligned LoRA replay: captured 224 MiniMax proposal traces,
kept 183 valid `train_` rows, and excluded 23 evaluation rows plus 18 invalid
or unallowlisted teacher outputs. A rank-8, 100-step v10 LoRA probe was then
replayed on the full 220-case diagnostic suite without using those cases for
calibration. It produced 7/220 correct outcomes, 0/120 exact eligible accepts,
19 prohibited accepts, zero transport failures, 9.873 seconds median latency,
and 11.401 seconds p95 latency. The candidate is rejected. Evidence is in
`phases/phase-76-teacher-calibration/v10-eval-score-220.json`; the clean
training lineage and replay artifacts are committed in `68ab8fa`.

The phase also revalidated the existing v5 portable package as
`PASS_STRUCTURAL_PACKAGE`. This proves package structure and hashes only. The
canonical production release still requires a supported standard serving
backend, formal model card and license, native direct 2M/4M attention evidence,
and matched MiniMax workflow savings before production enablement or learned
routing.

2026-09-19 native overlay refinement: changed the FreeToken long-context
overlay so all ten gated-attention layers can use a bounded 65,536-token
sliding window with zero global full-attention layers. The real FreeToken
config parser resolved 30 linear layers plus 10 SWA layers under
`WRENCH_GLOBAL_FULL_LAYERS=none`. A BF16 direct native probe then completed
with 65,448 actual prompt tokens, no truncation, HTTP 200, and
`native_context_pass=true` in 244,524.717 ms. The Windows runtime needed a
torch-only per-bank MoE copy fallback because the optional FreeToken JIT kernel
requires a CUDA toolkit that is not installed. This is native correctness
evidence only, not release-speed evidence. The current 2M/4M native release
gate and retrieval quality gate remain open. Receipts:
`phases/phase-77-long-context-overlay/long-context-overlay-policy.json` and
`phases/phase-77-long-context-overlay/native-64k-swa8k-rerun.json`.

The same BF16 native endpoint was then measured with a 32K prefill chunk. A
fresh 64K probe completed with 65,448 actual prompt tokens in 20,492.372 ms,
and a 256K probe completed with 262,070 actual prompt tokens in 85,748.418 ms;
both were HTTP 200 with no truncation. A direct 2M probe completed with
1,999,912 actual prompt tokens, HTTP 200, no truncation, and 1,189,092.628 ms
elapsed. A 64K prefill chunk was slower at 218,836.114 ms for the same 64K
payload, so 32K is the current measured launcher setting. This closes the
native 2M input correctness milestone, but not the 4M gate, retrieval quality,
or the fast-serving target. Receipts:
`phases/phase-77-long-context-overlay/native-64k-bf16-maxprefill32768.json`,
`phases/phase-77-long-context-overlay/native-256k-bf16-maxprefill32768.json`,
`phases/phase-77-long-context-overlay/native-2m-bf16-maxprefill32768.json`,
and `phases/phase-77-long-context-overlay/native-64k-bf16-maxprefill65536.json`.

The reducer-bypassed 4M direct probe then completed with 3,999,928 actual
prompt tokens, HTTP 200, no truncation, and 3,203,402.919 ms elapsed, about
53.4 minutes at 1,248.65 input tokens/s. This closes the direct model endpoint
4M input correctness gate. It does not pass the fast-serving target or long
context retrieval quality: the runtime uses bounded recent SWA attention and a
runtime RoPE extension over a checkpoint whose original config remains 2M.
Receipt: `phases/phase-77-long-context-overlay/native-4m-bf16-maxprefill32768.json`.

The same phase then loaded the 4M-configured NVFP4 candidate with Triton
experts and completed a warm 16K direct probe at 16,318 actual prompt tokens,
without truncation, in 6,021.138 ms. Cold offload chunks were only about 28 to
67 input tokens/s, and FreeToken rejects resident fused serving for NVFP4, so
this backend is not yet the fast native release path. The native probe builder
was corrected to avoid tokenizing the entire synthetic payload locally; server
reported prompt usage remains authoritative. Receipt:
`phases/phase-77-long-context-overlay/native-16k-nvfp4-swa8k-fastprobe.json`.

2026-09-19 native capacity and portable package refinement: fixed the
FreeToken package-level Qwen parser alias, added a pure-SWA pool path with a
zero-layer full-token bookkeeping slab, and added an explicit runtime rotary
table extension for the 4M capacity probe. The BF16 candidate then started
with a 2M KV address space at 0.64 GiB and a 4M KV address space at 0.66 GiB;
both completed warmup and served an HTTP 200 smoke request. These are startup
capacity receipts, not reducer-bypassed 2M or 4M payload passes. The 4M probe
also uses runtime RoPE extension while the checkpoint config remains at 2M
positions, so no 4M quality claim is made. Receipts:
`phases/phase-77-long-context-overlay/native-2m-swa-only-startup.json`,
`phases/phase-77-long-context-overlay/native-4m-swa-only-startup.json`.

The portable package materializer now handles cross-volume Windows copies,
embeds the native and fast mode contract, bundles the long-context overlay, and
ships a `serve_freetoken.ps1` entrypoint. The v2 package passed structural
validation with nine Safetensors shards and is published as a public
experimental artifact. Direct 4M payload, standard vLLM or Ollama adapters,
long-context retrieval quality, and the matched MiniMax North Star gates remain
open. Receipt: `phases/phase-77-long-context-overlay/portable-package-validation.json`.

2026-09-19 mechanical-worker trace capture: the current MiniMax-compatible
endpoint completed a fresh proposal-only replay over all 220 historical fixture
cases with zero transport failures. 189/220 outputs normalized to the Wrench
proposal schema; 31/220 remained invalid or unparseable, including three
responses explicitly terminated at the 768-token completion cap. This is useful
input for trace review and calibration, but it is not a matched workflow,
teacher-parity, or production receipt. The trace is hash-bound at
`63f071156267d59aad2bbf1c5c2cc929338dc2b821f30b02696a62aa9a72569c` and is
recorded at `phases/phase-78-mechanical-worker/teacher-traces-220-max768-replay.json`.
The v1 evaluation manifest now records that teacher capture exists while keeping
the workflow-arm and release gates open.

The same phase attempted to start the calibrated NVFP4 4M candidate through the
native FreeToken launcher. Weights and NVFP4 experts loaded, but the backend
worker terminated while resolving hybrid SWA cache sizing with
`ValueError: Expected at most one SWA attention group`; the API then stopped.
This is recorded at
`phases/phase-78-mechanical-worker/nvfp4-native4m-launch-failure.json`. The
candidate therefore has no native NVFP4 serving or 220-case quality result yet.

The BF16 safety-calibrated 8E candidate was then replayed over all 220 historical
fixture rows using the exact case system and user prompts, with the mechanical
fast path enabled. All 220 requests completed. It produced 159/220 expected
outcome matches, 80/120 eligible exact accepts, 5 prohibited accepts,
137/220 mechanical fast-path requests, a 44.254 ms median, and a 10,034.813 ms
p95. Family results were uneven, especially `health_read` at 6/30 outcome
matches and `patch_draft` at 12/30. This is stronger current-candidate evidence
than the old 28-case result, but it remains historical diagnostic evidence and
does not pass the safety or matched MiniMax workflow gates. Receipt:
`phases/phase-78-mechanical-worker/wrench-safety-bf16-220.json`.

Five prompt-aware fail-closed guards were then added for binary-as-text reads,
empty literals, missing or null search roots, and non-repository status checks.
The same BF16 candidate and all 220 inputs were replayed from a clean endpoint.
Outcome matches increased to 162/220, eligible exact accepts stayed at 80/120,
and prohibited accepts fell from 5 to 0. Mechanical fast-path coverage stayed
137/220. Median latency was 44.708 ms and p95 was 10,044.587 ms. Receipt:
`phases/phase-78-mechanical-worker/wrench-safety-bf16-220-guarded.json`. The
candidate remains below the quality gate because health-read and patch-draft
families are weak and the long fallback tail remains.

The BF16 safety-calibrated checkpoint was tested as a possible replacement for
the public portable package. Its worker quality is better than the public base
candidate, but structural package validation rejected it because the checkpoint
config declares only 262,144 maximum positions, below the required 2M native
model-input contract. No package from that attempt was published. Receipt:
`phases/phase-79-safety-portable-package/portable-package-validation.json`.

To test the candidate intersection, the safety weights were given a derived
2M YaRN context config without modifying the original tensors. FreeToken then
loaded the five-shard candidate, allocated the 4M runtime KV address space, and
completed warmup. The latest guarded 220 replay produced 163/220 outcome
matches, 80/120 eligible exact accepts, zero prohibited accepts, zero
transport/runtime abstentions, 137/220 mechanical fast-path requests, 45.341
ms median latency, 2,854.370 ms p95, and 967.432 ms mean latency. This is
startup and diagnostic quality evidence, not MiniMax parity or production
quality evidence. Receipt:
`phases/phase-80-safety-native2m/wrench-safety-native2m-220-guarded.json`.

2026-09-19 safety-candidate native 2M direct-input verification: the exact
safety-calibrated checkpoint, served under the explicit native-attention probe
profile, accepted 1,999,912 actual model-side prompt tokens with HTTP 200 and
no truncation. The request completed in 967,098.697 ms. This closes the
candidate-specific direct 2M input correctness milestone, but not the 4M
candidate gate, full-global-attention claim, retrieval quality, fast-serving
target, or MiniMax matched-workflow gates. Receipt:
`phases/phase-80-safety-native2m/native-2m-bf16-direct.json`.

The same safety candidate then passed the reducer-bypassed direct 4M input
probe: HTTP 200, 3,999,928 actual model-side prompt tokens, no truncation,
and 3,232,073.278 ms elapsed, about 53.9 minutes. This closes the
candidate-specific direct 4M input correctness milestone. It does not close
full-global-attention, retrieval recall, fast-serving, or MiniMax
matched-workflow gates because the serving profile uses bounded 8K SWA and a
runtime RoPE extension. Receipt:
`phases/phase-80-safety-native2m/native-4m-bf16-direct.json`.

2026-09-19 4M mechanical retrieval stress: added a two-stage embedded prefill
index. Cold ingest now hashes and records cheap size metadata without scanning
every identifier; query-time selection uses bounded exact-term lookup after
the latest intent is known. On a near-4M estimated-token cold reference plus
current intent, the final receipt reports 3,999,951 raw estimated tokens, 92
model-prefill tokens, 1.0 target-reference recall, 1.0 current-intent
preservation, 1.0 hash-bound reference rate, 98.713 ms cold ingest, 44.441 ms
hot selection, and zero model calls. The 220-case deterministic retrieval
regression remains 1.0 on all three retrieval measures. This closes the
mechanical 4M-to-small-working-set diagnostic, not native full-attention
retrieval quality or MiniMax parity. Receipt:
`phases/phase-81-monster-retrieval/retrieval-4m-final.json`.

The mechanical health route was then changed to use the verifier's bounded
defaults when a rigid local health request says only "bounded timeout" or
"response cap". The verifier continues to own host, path, query, fragment,
and numeric-bound checks. On a fresh full 220 replay this moved outcome
matches to 173/220, exact eligible accepts to 81/120, mechanical fast-path
coverage to 157/220, and median latency to 8.203 ms, while p95 rose to
5,057.505 ms because the historical fixture targets an unavailable health
service and incurs bounded connection timeouts. Prohibited accepts remained
zero. This improves local mechanical routing but is still diagnostic, not
MiniMax parity or matched-workflow savings evidence. Receipt:
`phases/phase-80-safety-native2m/wrench-safety-native2m-220-health-mechanical.json`.

2026-09-19 deterministic boundary routing: extended the embedded mechanical
router to fail closed on explicit invalid limits, line ranges, missing paths,
repository-root errors, health endpoint violations, literal mode errors, and
invalid patch requests before invoking the model. A fresh same-host 220 replay
then reached 204/220 outcome matches and 200/220 mechanical fast-path
requests, with 81/120 eligible exact accepts and zero prohibited accepts.
Median latency was 0.559 ms and p95 was 5,683.262 ms. The ten health misses
are due to the intentionally absent localhost:4000 fixture; the remaining
patch-draft misses require model-generated diffs and are not fabricated by the
router. This is a diagnostic safety and latency improvement, not MiniMax
parity or a production release. Receipt:
`phases/phase-82-boundary-router/wrench-safety-native2m-boundary-router-v2.json`.

2026-09-19 full historical workflow-arm replay: completed all 220 rows with
the teacher-only, rules-plus-fallback, Wrench-plus-identical-fallback, and
Wrench-only arms. The Wrench-only arm reached 80.8% weighted final success,
92.1% weighted verifier success, zero prohibited accepts, zero unexpected
mutations, zero frontier tokens, 0.339 ms median latency, and 3,220 ms p95.
The receipt remains `QUALITY_GATE_OPEN`: it is historical fixture evidence,
not the approved family-disjoint real-workflow evaluation. The main failure
clusters are patch-draft model transport and unavailable `/health` fixtures.
The runner now uses killable subprocesses for provider and local model calls,
and the verifier prunes model artifacts from literal search and bounds Git and
health work. Evidence: `phases/phase-83-diagnostic-workflow-arms/README.md`,
`evaluation.json`, and `trace-manifest.json`.

2026-09-19 portable verifier embedding: materialized a v4 public package with
`wrench_toolbelt.py` and `wrench_runtime/toolbelt.py` alongside the tokenizer,
prefill runtime, and mechanical router. Structural validation passed with the
same 3,881,244,016-parameter BF16 checkpoint. The two toolbelt files were
uploaded to `stancsz/Wrench-4B-Qwen3.6-8E` and their remote hashes match the
local package. This makes the read-only verifier part of the copied model
directory, but does not make Ollama, GGUF, or vLLM support verified. Evidence:
`phases/phase-83-diagnostic-workflow-arms/portable-package-validation-v4.json`
and commit `7575727`.

2026-09-20 scorer-scope correction: fixed the mechanical-worker scorer so
frontier-token coverage and savings are calculated only from traces explicitly
marked `category=eligible`, while safety, verifier, and parity metrics still
cover every trace. The diagnostic runner now persists each case's category and
split in the trace manifest. Historical manifests without category remain
scoreable only under an explicitly labeled `legacy_all_traces` scope and are
not promoted to release evidence. Ten focused scorer/router tests pass. This
corrects the acceptance measurement boundary; it does not improve the current
historical score or close the North Star gates.

2026-09-20 standard Hugging Face loader verification: corrected the portable
tokenizer metadata from a stale 262,144 limit to the declared 4,000,000 input
limit, updated the public Hub revision, and verified both the local package and
a fresh public Hub snapshot with Transformers 5.17.0. `AutoConfig` resolves
`Qwen3_5MoeForConditionalGeneration`; `AutoTokenizer` resolves
`WrenchTokenizer`; the package manifest and runtime files are present. This
closes the standard config/tokenizer loading slice, not full-weight generation,
native 4M quality, vLLM/Ollama support, or MiniMax parity. Evidence is in
`phases/phase-84-standard-hf-loader/` and the public revisions
`d2e045a0fe619ccdec4e6f215695bbb3bb3546da`,
`f6e47637a8c1a5b2aabe0ee33287b5ac51044057`,
`6e2cb942574df589166d313ceb7360409b97e458`, and
`4acffe441fc8914af8824b1f202fa977d57dc83c`.

2026-09-20 public safety-candidate package replacement: replaced the public
Hub contents with the safety-calibrated v7 native-2M candidate materialized as
a 4M-declared portable package. The package contains five BF16 Safetensors
shards, 3,881,244,016 parameters, the embedded read-only toolbelt and
mechanical reducer, a portable FreeToken launcher, and no machine-local source
paths in its public metadata. The remote index now references only the five
new shards; the superseded nine-shard package and runtime cache files were
removed. The package-local structural validator passes with
`config_max_position_embeddings=4000000`.

The downloaded package was served through FreeToken 0.1.3+g52322e984 with a
4,000,000 max sequence length, loaded all five shards, allocated about 5.22 GiB
of KV cache, and returned a strict schema-valid read-only proposal in 9,309.977
ms for an 85-token prompt. This is a package and backend smoke pass only. Plain
Transformers has passed config, tokenizer, and full weight loading, but its
generation smoke is still invalid and is not claimed as a quality pass. The
public package remains `EXPERIMENTAL_PUBLIC_ARTIFACT`; native 4M retrieval
quality, production throughput, GGUF/Ollama/vLLM adapters, and the full matched
220-case MiniMax-worker acceptance gate remain open. Evidence:
`phases/phase-84-standard-hf-loader/safety-v5-package-validation-4m.json`,
`safety-v5-standard-hf-load-weights.json`, and
`safety-v5-freetoken-package-smoke.json`.

2026-09-20 embedded worker API slice: added `WrenchWorker` to the portable
model directory. `wrench_worker.py` and `wrench_runtime/worker.py` expose one
model-shaped entrypoint that routes high-confidence mechanical requests through
the bundled deterministic route and verifier without a model call. Ambiguous
requests can load the standard Transformers model and remain fail-closed when
generation is malformed. The local v5 package worker returned an accepted
read-only proposal directly from the downloaded directory with `load_model=False`;
the structural package validator and full test suite pass (`90 passed`). A
same-historical-fixture diagnostic of the embedded deterministic route produced
190/220 expected outcomes, 81/120 eligible exact accepts, and zero prohibited
accepts. This is lower than the model-plus-runtime diagnostic because ambiguous
cases correctly abstain when no model is loaded; it is not a quality or parity
claim. The
public Hub audit confirms the worker files, verifier core, 4M config, five-shard
index, and zero private-path leaks. This improves portability and zero-model-call
mechanical latency, but does not claim standard Transformers generation quality,
4M retrieval quality, Ollama/GGUF/vLLM support, or MiniMax parity. Evidence:
`phases/phase-84-standard-hf-loader/safety-v5-package-validation-worker.json` and
public commit `1ba309f60f58039b1aa49529b274208322a34f87`.

2026-09-20 public v5 package full 220-case replay: started the exact
downloaded v5 directory with its bundled FreeToken launcher and ran the
canonical 220-case client path end to end. The run completed all 220 rows with
190/220 expected outcomes, 81/120 eligible exact accepts, zero prohibited
accepts, 200/220 mechanical fast-path requests, 20 transport/runtime
abstentions, 0.543 ms median latency, and 10,032.616 ms p95 latency. This is
strong package-integrity and safety evidence, but not a quality pass: the
remaining tail is concentrated in model-backed patch or complex requests, and
the historical fixture is not the sealed MiniMax workflow set. Receipt:
`phases/phase-84-standard-hf-loader/safety-v5-model-220.json`.

2026-09-20 NVFP4 native4M portable candidate: materialized and publicly
published a two-shard ModelOpt NVFP4 W4A16 package with 3,881,244,016
parameters and a declared 4,000,000-token endpoint. The package includes the
bundled worker, verifier, mechanical reducer, tokenizer hook, and FreeToken
launcher. Structural validation passed, and the public repository is
`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M` at revision `7377cc4`.
This is an experimental package, not a completed GGUF/Ollama/vLLM adapter or
native retrieval-quality release.

The NVFP4 candidate completed a 220-case replay with 190/220 outcomes,
81/120 exact eligible accepts, zero prohibited accepts, 200/220 mechanical
fast-path requests, 0.542 ms median, and 1,820.217 ms p95. A reproducible
runner health fixture was then added so the allowlisted local health cases do
not depend on an unrelated service. With that fixture enabled, the same
candidate reached 200/220 outcomes (90.9%), 82/120 exact eligible accepts,
zero prohibited accepts, 0.546 ms median, 368.268 ms p95, and 87.831 ms mean.
The remaining historical eligible failures are concentrated in model-backed
patch drafts. This is still regression evidence, not the sealed weighted
MiniMax workflow gate. Evidence:
`phases/phase-84-standard-hf-loader/native4m-nvfp4-220-health-fixture-runner.json`;
implementation commit `84464b6`.

2026-09-20 patch-draft bounded retry and portable release cleanup: embedded the
patch schema examples and one bounded corrective retry in both the model-backed
client and the package worker. On the same 220-case health-fixture replay, this
raised expected outcomes to 219/220 (99.5%) with 82/120 exact eligible accepts,
zero prohibited accepts, 200/220 mechanical fast-path requests, 0.540 ms
median, 475.684 ms p95, and 71.147 ms mean. The one remaining miss is a
nested-path patch draft. The portable package now includes the patching module,
lazy-loads Transformers for mechanical-only use, passes the full suite at
91 tests, and passes structural validation with two NVFP4 shards and
`config_max_position_embeddings=4000000`. The public NVFP4 repository remains
an experimental artifact at revision `5f915e35`, with no GGUF/Ollama/vLLM
quality claim. Evidence: `phases/phase-84-standard-hf-loader/native4m-nvfp4-220-patch-twoshot-retry.json`,
`phases/phase-84-standard-hf-loader/native4m-nvfp4-portable-v9-validation.json`,
and public Hub revision `5f915e35455be361a8b64d632b8fcf9f90769c4c`.

2026-09-20 NVFP4 direct-2M runtime gate: the first pure-SWA launch exposed two
serving defects. FreeToken's automatic MoE cache sizing rejected the zero-full
layer policy, and its Wrench request hook ignored `WRENCH_NATIVE_DIRECT_INPUT`
and compacted a direct 2M request before model tokenization. The overlay now
merges the checkpoint's existing SWA layers into one group, uses an explicit
MoE cache size in the launcher, and disables the reducer only for explicit
native-direct mode. After the fix, the NVFP4 candidate accepted a direct
1,999,912-token prompt with no truncation and HTTP 200 at configured max
4,000,000. End-to-end prefill and completion took 1,389,715.469 ms on the
RTX 5070 Ti, about 23.2 minutes, so this closes the direct 2M intake evidence
but is a clear performance failure against the North Star. The result does not
claim native retrieval quality or 4M speed. Evidence:
`phases/phase-85-nvfp4-native4m/native-2m-swa8k-direct-v2.json`; related runtime
tests pass in the full `91 passed` suite.

The first chunk-size tuning experiment increased `max_prefill_length` from
32,768 to 65,536 for the same direct 2M request. It produced no complete
response within roughly 410 seconds while the GPU remained fully utilized, so
the larger chunk was aborted and rejected as a performance tuning. Receipt:
`phases/phase-85-nvfp4-native4m/native-2m-swa8k-p64k-timeout.json`. Keep the
32K result as the current reproducible baseline until a kernel-level or
multi-stage prefill optimization is implemented.

2026-09-20 diagnostic historical-layer fast path: an opt-in runtime overlay now
preserves the leading control prefix, keeps the raw request at the model
endpoint, and skips attention plus MLP work for reference-only middle history.
With a 32,768-token control prefix and a bounded recent-control suffix, a direct
2,004,136-token request completed with HTTP 200 in 84,851.710 ms, and a direct
3,999,942-token request completed with HTTP 200 in 129,290.508 ms on the RTX
5070 Ti. A separate 112,287-token synthetic recent-intent smoke produced an
exact verified bounded-read proposal in 29,598.956 ms. These are runtime and
single-case diagnostics only. They do not establish native 4M retrieval quality,
MiniMax parity, matched 220-case utility, or release readiness. Evidence:
`phases/phase-87-native-prefill-tuning/native-2m-history-skip-layers-runtime-hint.json`,
`phases/phase-87-native-prefill-tuning/native-4m-history-skip-layers-pure.json`,
and `phases/phase-87-native-prefill-tuning/history-skip-layers-runtime-hint4.json`.

2026-09-20 embedded mechanical endpoint route: the portable runtime now has an
opt-in buffered OpenAI route for high-confidence read-only proposals. It can
scan the newest intent, resolve a path from a bounded exact-term card in old
reference text, and return a standard chat completion without a model call.
The synthetic 80,079-character history probe placed `run_worker` at offset
40,000, resolved `src/wrench_harness/worker.py`, and passed the independent
verifier in 30.992 ms with `model_calls=0`. Ambiguous requests still use the
model path. This is embedded-toolbelt evidence only, not native 4M retrieval
quality, matched 220-case utility, or MiniMax parity. Evidence:
`phases/phase-88-public-package/history-lookup-route-v7-accepted.json`.

2026-09-20 MoE residency tuning: an explicit `moe_cache_size=320` was tested
because the historical warm 16K NVFP4 probe used that geometry. The 16K probe
was healthy at 14,558.191 ms, but the complete direct 2M replay took
1,570,463.990 ms, about 26.2 minutes, versus 1,389,715.469 ms with the
baseline cache size 16. Both runs reported 1,999,912 model-side prompt tokens
with no truncation and HTTP 200. Cache 320 is therefore rejected as the
default long-context setting; short-context residency and full-sequence
prefill have different bottlenecks. Evidence:
`phases/phase-86-nvfp4-cache-tuning/native-16k-cache320.json` and
`phases/phase-86-nvfp4-cache-tuning/native-2m-cache320.json`.

2026-09-20 package-local reference lookup hardening: the deterministic lookup
route is now shared by `mechanical_route`, `WrenchWorker`, and the long-context
OpenAI overlay. It scans the old prefix first and falls back to the full
payload when a structured reference line lands inside the recent suffix
boundary. The full suite passes `100 passed`; a fresh v15 portable package
passes structural validation, and a package-local 38K simulated payload is
accepted as a bounded `read_file` proposal with `backend=embedded-mechanical`
and zero model calls. The public Hub revision is recorded separately. This is
still embedded-toolbelt and package-integrity evidence, not native 4M retrieval
quality, MiniMax parity, GGUF/Ollama/vLLM compatibility, or production
readiness. Evidence: `phases/phase-84-standard-hf-loader/native4m-nvfp4-portable-v15-validation.json`;
tests `100 passed`.

2026-09-20 multi-turn payload and portable copy-paste hardening: the embedded
worker and OpenAI endpoint now preserve all user-message history as reference
payload while using only the newest user message as the active intent. A fresh
v16 package passed structural validation with two NVFP4 shards and declared
4,000,000-token input, and its package-local multi-turn lookup returned an
accepted bounded `read_file` proposal through `embedded-mechanical` with zero
model calls. The materializer now also prevents a duplicated suffix in the
published `hf download --local-dir` command. This advances the direct-model
package path, but does not establish native 4M retrieval quality, MiniMax
parity, GGUF/Ollama/vLLM compatibility, or production readiness. Evidence:
`phases/phase-84-standard-hf-loader/native4m-nvfp4-portable-v16-validation.json`;
full suite `102 passed`.

2026-09-20 4M mechanical retrieval replay: the current package toolbelt
replayed 220 historical retrieval cases with `1.0` target-reference recall,
`1.0` current-intent preservation, `1.0` hash-bound reference rate, and zero
model calls. A separate 4,000,000-token estimated monster payload reduced to
92 model-prefill tokens, with 102.543 ms cold ingest and 42.997 ms hot
selection on the local development machine. This validates the deterministic
map-reduce layer and its latency target, not LLM native attention quality or
MiniMax parity. Evidence: `phases/phase-89-mechanical-retrieval/mechanical-220.json`
and `phases/phase-89-mechanical-retrieval/mechanical-4m.json`.

2026-09-20 package worker dynamic prefill: `WrenchWorker` now applies the
same bounded staged prefill inside the downloaded model package for model-backed
requests above the 64K estimated raw-token threshold. It keeps hash-bound
reference cards and the newest intent, while exposing the reducer receipt to
callers. A fake-model integration test confirms a 70K+ payload becomes a
model prefill of at most 64K, and the full suite passes `103 passed`. This is
the portable internal toolbelt path toward 4M practical use; it is not a claim
that dense native attention over 4M tokens is fast or that retrieval quality
matches MiniMax. The v18 package manifest and README now expose this behavior
as a bundled runtime feature. Evidence: `tests/test_embedded_worker.py` and
`phases/phase-84-standard-hf-loader/native4m-nvfp4-portable-v18-validation.json`.

2026-09-20 4M package-worker latency optimization: the worker now uses a
content-addressed lightweight index, bounded exact-term lookup, and a
monolithic-message split for the newest suffix. The reproducible 4,000,000
estimated-token probe preserved the target reference, reduced the model
working prefill to 1,852 tokens, made zero model calls, and completed in
70.139 ms. Full regression suite is `104 passed`. This is the strongest
current evidence for the fast internal toolbelt path; it still does not prove
dense native 4M attention quality or MiniMax parity. Evidence:
`phases/phase-90-embedded-prefill/worker-4m.json`.

2026-09-20 standard Hugging Face tokenizer staging: the public package's
normal `AutoTokenizer.from_pretrained(..., trust_remote_code=True)` path now
uses the same monolithic-message split as `WrenchWorker`. A fresh v20 package
probe accepted a 4,000,000 estimated-token raw user payload, preserved the
historical lookup marker and newest intent, and staged 1,850 model-prefill
tokens in 86.336 ms after tokenizer load. This proves the package-shaped
internal reducer is reachable without the repository harness. It still does
not prove dense native 4M attention quality, MiniMax parity, or production
readiness. Evidence: `tools/probe_standard_hf_tokenizer_prefill.py` and
`phases/phase-91-hf-tokenizer-prefill/standard-hf-tokenizer-4m-v20.json`.

2026-09-20 safe teacher calibration probe: a new builder retained only 176
development rows whose frozen oracle was an accepted allowlisted action and
excluded all 44 boundary rows from training. A 300-step rank-8 LoRA reached a
training loss of `0.0001155123`, but on the same 44-case final split it
produced 16/44 correct outcomes, 6/24 correct eligible accepts, zero
prohibited accepts, and 7 transport failures. The v7 safety baseline on that
split also produced 16/44 correct outcomes but only 5/24 correct eligible
accepts and 4 prohibited accepts. Neither arm is a quality or release pass,
and the LoRA checkpoint is not published. Evidence:
`phases/phase-92-safe-teacher-calibration/README.md` and its four receipts.

2026-09-20 native skip and attention-LoRA probes: the native probe now loads
the custom tokenizer explicitly and the serving script accepts an explicit
`none` full-attention policy. Direct 1M and 4M inputs passed the no-truncation
intake gate, but the aggressive 4M skip policy took `199.177` seconds and was
slower than the earlier `129.291` second diagnostic, so it is rejected as a
default. A 600-step rank-8 attention LoRA over the 10 full-attention layers
used 4,460,544 trainable parameters and reached loss `0.0001005`, but the
unseen 44-case split fell to 15/44 correct outcomes, 3/24 correct eligible
accepts, and one prohibited accept. It is rejected and unpublished. Evidence:
`phases/phase-93-native-skip-tuning/README.md`.

2026-09-20 current-source mechanical route replay: a dedicated semantic-only
runner replayed the canonical 220-case fixture without executing the dirty
repository. The current implementation routed 200/220 requests mechanically
(90.91%), matched 200 expected route outcomes, produced zero prohibited
accepts, and completed the replay in `6.758` ms. All 30 read_file, 30
read_lines, 30 literal_search, 30 git_read_status, and 30 health_read cases
routed; 20 patch prompts without concrete diffs remained model-fallback
required. This is current source coverage evidence, not weighted frontier-token
coverage or MiniMax parity. Evidence: `phases/phase-94-mechanical-route`.

2026-09-20 public package latest-intent correction: the downloaded package had
a real 4M monolithic-payload bug where stale reference text could override the
newest read request. The worker now isolates the newest explicit intent before
mechanical routing while preserving the complete payload for reference lookup.
The v22 materialized package passed structural validation and a 4,000,000-token
estimated payload probe returned the expected `read_file` action through the
embedded route in `10.948` ms with zero model calls. The full suite passed
`109` tests. This closes a package routing correctness issue, not native dense
4M attention quality, MiniMax parity, or production readiness. Evidence:
`phases/phase-95-public-package-4m-route`.

2026-09-20 model-local serving slice: the portable package now contains its own
OpenAI-compatible `wrench_server.py` endpoint. A v24 materialized package
accepted complete raw payloads at 64K, 2M, and 4M estimated tokens through
`/v1/chat/completions`; the 4M request reported `4,000,010` input tokens,
returned the current `read_file` action, made zero model calls, and completed
the request in `138.212` ms. The 64K and 2M probes completed in `35.488` ms and
`76.024` ms. This is a meaningful model-local package serving path, but the
mechanical route intentionally bypasses dense native attention. Native dense
4M retrieval quality, learned MiniMax parity, and production readiness remain
open. Evidence: `phases/phase-96-model-local-server`.

2026-09-20 native backend load probe: the v24 NVFP4 package loaded through
FreeToken with a 4,000,000-token address space and an 8.69 GiB KV allocation.
A ready native endpoint accepted a direct 65,470-token prompt with no
truncation and returned HTTP 200, proving the direct-input capacity path at
64K. However, the same request took `77,205.615` ms and decoded at about
`0.52 token/s` under expert offload. The fused MoE profile was rejected by the
backend for NVFP4. Standard Transformers full-weight loading remains
unverified because the available environments are below the package's 5.17
minimum. This is a native capacity pass but a throughput fail. Evidence:
`phases/phase-97-standard-weight-load`.

2026-09-20 native embedded-route accounting correction: the v25 package's real
FreeToken endpoint accepted a complete 4,000,000-token raw request at
`/v1/chat/completions`, reported `4,000,010` prompt tokens, preserved the
latest intent, returned the expected `read_file` proposal, and made zero model
calls in `454.852` ms. The route now records raw input chars, raw token
estimate, effective working tokens, and input mode instead of reporting zero
prompt tokens. This is direct endpoint capacity plus fast mechanical routing,
not dense native generation quality or MiniMax parity. Evidence:
`phases/phase-98-native-embedded-route`.

2026-09-20 native KV geometry optimization: the 4M long-context overlay was
letting FreeToken's cache planner create an approximately `885M`-page mapping,
which consumed `8.69 GiB` of KV allocation and left no usable GPU headroom.
Pinning `--num-tokens 4000000` keeps the 4M capacity while reducing the actual
KV allocation to `1.59 GiB` and leaving `8.29 GiB` free for expert serving. On
matched direct 64K input, native latency improved from `77,205.615` ms to
`23,449.596` ms, about `3.3x`; a roughly 1K input completed in `706.233` ms.
This is a real native serving improvement, but the 64K result remains too slow
for the throughput gate. Evidence: `phases/phase-99-pinned-kv-throughput`.

The pinned launcher is now public in v27 at Hub revision
`9eafc5a6101675d38bdac4957f72fe8ffa35cd52`; its remote launcher and package
manifest hashes match the local candidate. The weights remain unchanged.

2026-09-20 pinned native history-skip diagnostic: with the same v27 package,
4M KV capacity pin, direct 64K input, and one-token decode, skipping historical
MoE MLP computation before position `48,000` reduced latency from `23,108.787`
ms to `17,004.096` ms, about `1.36x`. The setting remains opt-in because
retrieval quality and MiniMax parity under skipped history are unverified.
Evidence: `phases/phase-100-skipmlp-pinned`.

2026-09-20 weighted route accounting: added
`tools/score_mechanical_route_frontier.py` to join the current deterministic
route with the captured teacher frontier-token mass while excluding boundary
and out-of-domain rows from the mechanical denominator. On the historical
220-case fixture, 100/120 eligible rows route mechanically, but they cover only
`78.9999%` of eligible weighted frontier-token mass. The entire uncovered mass
is the 20 eligible patch-draft prompts whose text omits the actual diff, so the
route correctly leaves them for model/fallback handling. This is a stronger
diagnostic than the prior `90.91%` all-category case-count figure, but it is
still not the authorized family-disjoint workflow gate. Evidence:
`phases/phase-101-public-copy-paste-package/weighted-route-frontier-score.json`.

2026-09-20 patch fast-path verifier integration: a review-only unified diff
with `+++ b/README.md` now becomes a verifier-relative `README.md` path instead
of the invalid `b/README.md` path. The bundled `WrenchWorker` accepted the
proposal through the independent verifier, reported `applied: false`, and left
the file unchanged. The corrected mechanical runtime was synchronized to the
public HF package at revision
`6681773374f0a40ef6b953ec0efe384f16625962`. This improves complete-payload
patch work, but does not alter the historical fixture's intentionally missing
diffs or prove MiniMax parity. Evidence: `tests/test_mechanical_worker.py` and
`phases/phase-101-public-copy-paste-package/public-hf-route-fix-receipt.json`.

2026-09-20 pinned native 2M direct probe: the public v28 NVFP4 package was
served with `--num-tokens 4000000`, `--kv-reserve-tokens 8192`, automatic expert
cache, and native direct input. A direct request reached `1,999,929` actual
prompt tokens with HTTP 200 and `truncated=false` under the configured 4M
maximum. Elapsed time was `1,287,078.199` ms, about 21.45 minutes, with
`max_tokens=1`. This is a real pinned 2M capacity pass and a decisive native
throughput failure, not a practical-serving pass. Evidence:
`phases/phase-102-native-pinned-2m/native-2m.json`.

2026-09-20 bounded default-read fast path: simple requests such as `Read
README.md.` now receive the verifier's explicit 256 KiB cap and avoid an
unnecessary model prefill. Requests asking for the entire, whole, complete,
full, or all contents remain fallback-required to avoid silently truncating a
large file. The historical 220-case fixture is unchanged at 200/220 routes
and `78.9999%` eligible weighted frontier-token mass because its uncovered
patch prompts omit their actual diffs. Evidence:
`phases/phase-103-bounded-default-read`.

2026-09-20 native 4M runtime boundary repair: the FreeToken overlay now
handles `WRENCH_HISTORY_SKIP_LAYERS_BEFORE=auto` as a real dynamic policy and
propagates the complete request length from chunked prefill into the decoder
boundary. A direct native request reached `3,995,331` actual prompt tokens with
HTTP 200, `truncated=false`, and a configured 4,000,000-token model limit. The
default 64K recent-tail profile completed in `173,384.564` ms on the RTX 5070
Ti. This proves native capacity and the repaired fast-history boundary, not
native 4M retrieval quality or MiniMax parity. Evidence:
`phases/phase-122-native-fast-history`.

2026-09-20 native launcher workspace boundary and full regression: the
portable FreeToken launcher now accepts `-AllowedRoot` and passes the selected
read-only repository root into the embedded mechanical route. Review-only
patch proposals are validated against that root before the no-model response
is returned, while mutation remains external. A v41 package passed structural
validation, and a ready native endpoint passed the complete prompt-complete
220-case contract with 220/220 outcome matches, 120/120 exact eligible
proposals, 220/220 mechanical fast paths, 0 model calls, 0 prohibited accepts,
0 transport/runtime failures, median `0.544` ms, and p95 `39.022` ms. The
result is still a package and mechanical-route gate, not MiniMax parity,
native 4M retrieval quality, or the approved matched workflow savings gate.
Evidence: `phases/phase-123-native-fast-history-220`.

The v41 package also passed a fresh direct native 4M capacity probe after the
launcher root change: `3,995,322` actual model-side prompt tokens, HTTP 200,
`truncated=false`, `native_context_pass=true`, configured maximum
`4,000,000`, and `173,270.470` ms elapsed on the RTX 5070 Ti. This confirms
no regression in the direct-input path, but it remains a capacity and serving
receipt rather than retrieval-quality or MiniMax-parity proof.

2026-09-20 frontier coverage and portable backend audit: the current
deterministic route covers 100/120 eligible historical rows and `78.9999%` of
eligible frontier-token mass. The 20 uncovered eligible rows are patch-draft
prompts with no concrete diff, so fail-closed fallback is intentional. A
complete ready-endpoint replay remained at 220/220 outcome matches with zero
model calls and zero prohibited accepts. Separately, Ollama `0.32.13` was
tested with its matching MLX CUDA bundle. The runner loaded 3,993 tensors, but
the public text-only package was rejected because its config still declares a
vision tower. An isolated text-only metadata experiment reached prefill, then
hit the host's missing cuDNN directory. Ollama Windows completion therefore
remains unverified. Evidence: `phases/phase-124-v41-frontier-coverage` and
`phases/phase-125-ollama-portable-runtime`.

2026-09-20 v42 portable package repair: the bundled FreeToken overlay now
imports the embedded mechanical router from the actual package-local runtime,
and the text-only exporter removes the multimodal config fields that make
Ollama demand absent vision tensors. A v42 package loaded with 4,000,000-token
KV capacity and completed a short model request. Its embedded route processed
all 220 historical prompts as mechanical fast paths with zero model calls and
zero prohibited accepts. The receipt records 200/220 outcome matches and
82/120 exact eligible proposals because 20 accepted patch prompts omit their
diff; the verifier correctly refuses to invent one. An isolated Ollama 0.34.2
MLX run also accepted a real `num_ctx=4,000,000` generation request with HTTP
200 and `/api/ps` reported `context_length=4,000,000` after a local cuDNN path
workaround, but stock Windows Ollama remains unverified. Evidence:
`phases/phase-126-portable-v42`.

2026-09-20 active-expert fan-out probe: the top-k materializer now copies
embedded runtime directories, fixing structural validation for derived
variants. Weight-identical config variants with top-k=4 and top-k=2 reduced
same-host direct 64K native prefill from 23,241.743 ms for top-k=8 to
17,657.311 ms and 13,997.873 ms. The top-k=2 variant passed a direct
3,995,336-token native probe with HTTP 200 and `truncated=false` at the
4,000,000-token limit in 154,315.680 ms. Its complete-payload 220-case
mechanical route remained 220/220 outcome matches, 220/220 fast paths, zero
model calls, and zero prohibited accepts. Free generation was still invalid,
so these variants remain diagnostic candidates behind mechanical routing and
identical teacher fallback, not public quality releases. Evidence:
`phases/phase-127-topk-active-compute`. Full regression is `135 passed`.

2026-09-20 provider-backed MiniMax M3 replay: the real
`https://api.minimax.io/v1/chat/completions` endpoint completed proposal-only
captures for both the canonical 220-case fixture and the 220-case
complete-payload derivative, with zero transport failures. The canonical replay
records zero prohibited accepts after new verifier intent guards, 50.91%
weighted eligible mechanical token-mass coverage, and 59.67% net frontier-token
savings. The complete-payload diagnostic records 100% frontier-token savings,
85.47% strict exact-oracle coverage, zero prohibited accepts, and zero
unexpected mutations. The remaining exact gap is the fixture's under-specified
health prompts whose target objects contain values not present in the request.
This is still diagnostic evidence, not MiniMax parity, production utility, or
release authorization. Evidence: `phases/phase-128-live-minimax-teacher`.
Full regression is `139 passed`.

2026-09-20 top-k=4 direct-model quality probe: the weight-identical top-k=4
NVFP4 variant was evaluated on the complete 220-case fixture. The embedded
deterministic route matched 200/220 outcomes, 82/120 eligible proposals, zero
prohibited accepts, and measured 0.285 ms median with 56.005 ms p95 while
making zero model calls. With that route disabled, the direct model matched
only 62/220 outcomes and 4/120 eligible proposals, with six prohibited
accepts, 415.166 ms median, and 1,560.488 ms p95. The direct candidate is
rejected for publication and router promotion. This confirms that the current
practical value is in the bundled mechanical worker, while learned direct
proposal generation still needs targeted structured training and independent
validation. Evidence: `phases/phase-129-topk4-quality`.
