# Goal: prove useful local selective offload for routine developer-tool work

Status: active
Updated: 2026-09-17
Owner: repository agent

## Outcome

Build a local Wrench component that can complete only a small, clearly eligible
subset of routine developer-tool work more cheaply or quickly than the stronger
model path, without reducing final task success or weakening execution controls.
Every uncertain, unsupported, risky, malformed, or failed case preserves the
original request and falls back cleanly.

The first candidate path is a task-specialized sparse coding model reduced from
an officially licensed base checkpoint, if and only if the checkpoint's actual
architecture supports safe structural pruning and the resulting candidate passes
the gates below. Deterministic rules plus cloud fallback remains an acceptable
final result.

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
  usage, routing entropy, token counts, and retained-expert selection rule.
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
