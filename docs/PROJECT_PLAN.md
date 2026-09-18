# Project Plan: Wrench Qwen3.6 Expert-Tier Evaluation - Selective Offload & Escalation

> **Evidence status (2026-09-17):** This plan is an execution hypothesis, not a
> release claim. The local Qwen3.6-35B-A3B artifact is an NVIDIA ModelOpt
> NVFP4/FP8 package. Its verified checkpoint receipt is
> [`phases/phase-1-checkpoint-facts/checkpoint-facts.json`](../phases/phase-1-checkpoint-facts/checkpoint-facts.json).
> It is not a safe source for tensor slicing. Any `<4B`, VRAM, throughput,
> quality, or token-savings target remains unearned until the named measurement
> gate for that phase passes.

Wrench remains proposal-first and fail-closed. “Autonomous completion” below
means an automatically proposed and independently verified result; it does not
grant the model arbitrary shell access, credentials, or unsupervised writes.

## Current model identity

There are now three experimental checkpoints, all pruned from Qwen3.6-35B-A3B
using real per-layer router telemetry. The compact 8-expert candidate reports
3,881,244,016 parameters and has an ideal INT4 weight-only estimate of about
1.84 GiB. The practical 16-expert candidate reports 4,888,532,336 parameters
and has an ideal INT4 estimate of about 2.32 GiB. The expanded 32-expert
candidate reports 6,903,108,976 parameters and has an ideal INT4 estimate of
about 3.28 GiB. Removing unused vision tensors yields text-only W4A16 NVFP4
FTW artifacts of 3.19 GiB for 8 experts and 3.72 GiB for 16 experts; both
passed bounded CUDA smokes. The latest 16-expert artifact has an experimental
calibration pass, but neither tier is approved, quality-evaluated, or
release-ready.

## Execution status

- **Phase 1, checkpoint facts:** complete for the local NVFP4 artifact. The
  receipt is hash-bound, and structural slicing is explicitly rejected for this
  packed source.
- **Phase 2, dataset audit:** complete as a mechanical audit. The three local
  JSONL files contain 5,000 parseable rows, but they are not approved training
  data. The audit reports substantial web/research and finance/crypto content,
  so filtering, licensing review, and Wrench task-family labeling are required
  before calibration or SFT.
- **Phase 3, source feasibility:** official source identified and hash-bound at
  revision `995ad96eacd98c81ed38be0c5b274b04031597b0`; the local-state record
  now points to the acquired checkpoint and Phase 22 validation receipts.
- **Phase 4, task portfolio:** proposed family-disjoint scope is frozen in
  `phases/phase-4-task-portfolio/portfolio.json`; human approval is pending.
- **Phase 6, runtime compatibility:** the current global Transformers 4.57.1
  cannot load the Qwen3.6 architecture. A project-scoped requirement and
  non-mutating check report global `NOT_READY`; an isolated Transformers 5.17.0
  environment with the existing PyTorch reports runtime `READY` without loading
  weights. Meta-tensor instantiation of `Qwen3_5MoeForConditionalGeneration`
  also passes; actual weight loading and GPU execution remain unverified.
- **Phase 7, NVFP4 runtime smoke:** Docker CUDA and Qwen/ModelOpt resolution
  pass, but vLLM 0.29 engine startup stops on unavailable UVA before loading
  weights. No generation evidence exists yet.
- **Phase 8, FreeToken runtime smoke:** the matching FreeToken runtime loaded
  the local `.ftw` weights and expert banks with bounded offload, completed
  warmup, and returned the exact bounded `WRENCH_RUNTIME_OK` response through
  `/v1/chat/completions`. This is runtime evidence only, not quality,
  throughput, pruning, or release evidence.
- **Phase 9, execution boundary:** `src/wrench_harness/core.py` now provides a
  fail-closed, read-only verifier for the six proposed portfolio actions. Its
  boundary suite passes 4 tests and proves no patch application or generic
  shell capability.
- **Phase 10, Qwen shadow proposal:** the local Qwen runtime emitted an exact
  `wrench.proposal.v1` read proposal and the independent boundary accepted it
  without mutation. FreeToken lacks constrained JSON decoding, so schema
  validation remains the safety gate. This is one integration smoke case, not
  a quality or workflow benchmark.
- **Phase 11, source acquisition gate:** the guarded preflight confirmed the
  71.9 GB unquantized source is absent, sufficient target disk exists, and the
  command refuses transfer without `--confirm-71gb`. No output directory or
  network transfer was created.
- **Phase 12, pruning-source validator:** an architecture-aware metadata gate
  now rejects the local packed FTW/NVFP4 package before any tensor-slicing code
  can run. The full test suite passes 5 tests; no weights were modified.
- **Phase 13, portfolio boundary evaluation:** 10 deterministic portfolio
  cases pass through the verifier with zero prohibited accepts. This validates
  the execution boundary only; the portfolio remains pending human approval
  and no model-quality claim is made.
- **Phase 14, model-output parser:** exact JSON-only model responses now route
  through the verifier; decorated or malformed responses abstain. The full
  test suite passes 6 tests. This is a parser-boundary result, not a model
  quality result.
- **Phase 15, local Qwen adapter:** a localhost-only OpenAI-compatible client
  now checks endpoint policy, response bounds, model identity, and strict
  parser routing. The mock-server suite passes 7 tests. This is adapter-boundary
  evidence only.
- **Phase 16, routing guard:** finite attempts, circuit opening, operator
  bypass, and hash-bound reset are implemented and covered by 8 passing tests.
  Durable restart, alerting, cancellation, and rollback evidence remain open.
- **Phase 17, router state:** schema- and configuration-hash-bound state
  persistence and recovery are covered by 9 passing tests. Process-crash
  simulation, alerting, cancellation, and rollback evidence remain open.
- **Phase 18, cancellation and events:** cooperative cancellation plus
  circuit, reset, and bypass events are covered by 10 passing tests. Blocking
  interruption and external alert delivery remain unproven.
- **Phase 19, real Qwen adapter path:** the actual local FreeToken/Qwen runtime
  produced a strict proposal that passed the localhost adapter and independent
  verifier. This is one real integration receipt, not a quality benchmark.
- **Phase 20, performance smoke:** one loose prompt abstained on invalid JSON;
  an exact-schema retry passed in 1,923.364 ms with 112 reported total tokens.
  The paired attempt receipt is diagnostic only, not a throughput benchmark.
- **Phase 21, Qwen shadow portfolio:** five accepted-action shapes passed
  through the real local Qwen runtime, adapter, and verifier. This is shadow
  observation only; the portfolio remains pending approval and no quality
  claim is made.
- **Phase 22, source inspection:** the explicitly authorized acquisition
  fetched all 38 requested files to `D:\\models\\Qwen3.6-35B-A3B`. The local
  checkpoint contains 26 safetensors shards with the exact official index total
  of 71,903,645,408 bytes. Metadata validation reports `eligible: true`, no
  missing shards, and no rejection reasons. This permits architecture-aware
  router profiling design; it does not prove pruning quality, loadability,
  throughput, or workflow value.
- **Phase 23, expert size estimate:** a header-only scan of all 1,045
  safetensors reports 35,951,822,704 BF16 tensor elements and 33,017,561,088
  routed-expert elements. Retaining 8 experts per MoE block estimates 3.945B
  total parameters, while 16 estimates 4.978B. This is the first measured
  candidate inside the 3 to 4B target, but it is not a pruned or calibrated
  model.
- **Phase 24, provisional structural prune:** a streaming pruner produced an
  8-expert-per-MoE-block BF16 checkpoint outside Git. Transformers loaded it on
  CUDA and counted 3,881,244,016 actual parameters. The deterministic smoke
  generated 8 tokens, but its output is not a quality pass. Expert indices 0
  through 7 are provisional until router profiling selects a Wrench-specific
  set.
- **Phase 25, router profile and three tiers:** the real NVFP4 teacher completed
  20 provisional Wrench prompts across 40 routed layers. Per-layer selection
  receipts drive new 8-expert, 16-expert, and 32-expert BF16 candidates. All
  three load and forward on CUDA. ModelOpt produced packed W4A16 NVFP4 exports
  for the 8- and 16-expert candidates. Removing unused vision tensors yields
  text-only FTW packs of 3.19 GiB and 3.72 GiB, and both passed bounded
  FreeToken generation smokes.
- **Next gate:** obtain explicit human approval for the frozen task portfolio,
  then compare the 8- and 16-expert text-only packed artifacts on a held-out
  approved Wrench evaluation split. Quantized size, loadability, and quality
  must be recorded separately. The 32-expert candidate remains BF16-only for
  now.
- **Phase 26 development comparison:** on ten fresh synthetic cases, both
  text-only FTW packs served every request but scored 0/10 exact verifier
  matches. Captured outputs repeatedly looped on malformed JSON. This is a
  provisional behavior signal only, not a final quality result or approval to
  favor the larger tier without calibration.
- **Phase 28 calibration probe:** a corrected 14-case synthetic holdout scores
  both calibrated tiers 9/14 in BF16 and 7/14 after NVFP4 packing. Exact
  proposal-object matches are 6/14 for 8E BF16, 6/14 for 8E FTW, 4/14 for
  16E BF16, and 3/14 for 16E FTW. These are provisional verifier receipts
  only. Human portfolio approval, broader held-out quality, and production
  enablement remain open.
- **Phase 29 unseen packed comparison:** on a separate 28-case synthetic
  fixture with unique IDs, 8E scored 8/28 verifier outcomes and 7/28 exact
  proposal objects; 16E scored 9/28 and 7/28. The 16E edge is small and does
  not establish usefulness, workflow value, or release readiness.
- **Phase 30 corrected calibration lineage:** accepted read limits were fixed
  to exceed current file sizes, and both generators now write hash-stable bytes
  on Windows. Fresh packed results on the corrected 14-case holdout are 5/14
  verifier and 3/14 exact proposals for 8E, versus 7/14 and 5/14 for 16E.
  On the corrected 28-case unseen fixture they are 9/28 and 9/28 for 8E,
  versus 10/28 and 7/28 for 16E. The result remains development-only.

## 1. Executive Summary & Core Objective

The objective of **Wrench-Code-4B-Qwen3.6-8E** is to validate a high-velocity,
sub-4-billion-parameter local model specialized in developer-tool workflows,
repository navigation, noise compaction, and deterministic code repair.

The Wrench operates as a **first-line defensive gateway**:
1. **Autonomous Completion (Low-Level Tasks)**: Independently executes routine, mechanical code edits and tool sequences when verified by deterministic tests (
pm test, pytest, linter = 0), costing **0 cloud tokens**.
2. **Self-Aware Competency & Clean Escalation (High-Level Tasks)**: Accurately identifies when a task exceeds its parameter boundary (or fails local test verification after 1 retry), packages a compacted failure payload (failing assertion + minimal diff), and seamlessly escalates to a frontier teacher model (localhost:4000/v1).

---

## 2. Architecture & Target Blueprint

`
                          [ Incoming Task / User Request ]
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       WRENCH-CODE-4B-QWEN3.6-8E               │
                 │   • Runtime: 4-bit / 8-bit (< 3 GB VRAM)      │
                 │   • Generation Speed: > 120 tokens/sec        │
                 └───────────────────────┬───────────────────────┘
                                         │
        ┌────────────────────────────────┼───────────────────────────────┐
        ▼                                ▼                               ▼
[Job A: Discovery]             [Job B: Compaction]             [Job C: First-Draft]
• Executes grep, cat           • Strips 50k raw logs           • Generates 1-pass patch
• Explores files locally       • Isolates error & stacktrace   • Runs deterministic test
        │                                │                               │
        │                                │                               ▼
        │                                │                    [Deterministic Verifier]
        │                                │                     (Exit Code 0 Check)
        │                                │                     ├── PASS -> ACCEPTED (0 paid tokens)
        │                                │                     │
        │                                ▼                     └── FAIL
        └──────────────────────> [Escalation Engine] <───────────────────┘
                          (Recognizes boundary / failure)
                                         │
                                         │ (Sends clean 1k-token payload)
                                         ▼
                         ┌───────────────────────────────┐
                         │   FRONTIER TEACHER (:4000)    │
                         │   Complex architectural logic │
                         └───────────────────────────────┘
`

* **Parameter Ceiling**: < 4.0 Billion parameters.
* **Serving Footprint**: < 3.0 GB VRAM (allowing full co-existence on a 16 GB RTX 5070 Ti).
* **Base Architecture**: Pruned/distilled from state-of-the-art coding teachers (Qwen3.6-35B-A3B / Qwen2.5-Coder-32B / Phi-4).

---

## 3. Five-Phase Implementation Roadmap

### Phase 1: Teacher Distillation & Pruning Strategy
* **Target Teacher**: Official frontier coding model / Qwen3.6-35B-A3B / Qwen2.5-Coder-32B.
* **Shrinkage Methodology**:
  - **Sequence-Level Distillation**: Feed curated agentic trajectories (pyromind/agentic-tool-call and glaive-function-calling) to the teacher to generate gold-standard, zero-fluff tool calls and repair diffs.
  - **Task-Guided Pruning (If MoE)**: Hook router logits on Qwen3.6-35B-A3B across 1,000 coding calibration tasks; isolate the top 16-32 hot coding experts per layer and excise the dormant ~224 non-coding experts, leaving a ~3.2B parameter dense/sparse core.
  - **Direct Base Downspring**: Alternatively, anchor on Qwen2.5-Coder-3B or Phi-4-mini as the pre-distilled base architecture.

### Phase 2: Supervised Fine-Tuning (SFT) & Specialization
* **Dataset Ingestion**: Utilize dataset/ in this repository:
  - gentic_tool_call_short_2k.jsonl: Enforces single-step and two-step deterministic tool execution.
  - gentic_tool_call_long_1k.jsonl: Multi-turn repository exploration and error handling.
  - glaive_function_calling_2k.jsonl: Strict JSON schema adherence and tool syntax.
* **Formatting & Optimization**:
  - Apply official Qwen/ChatML template with structured 	ool_calls blocks.
  - Train using QLoRA / Unsloth (Rank r=16, Alpha alpha=32) targeting all linear projection layers.
  - Quantize final artifact to 4-bit (AWQ / GPTQ / ModelOpt NVFP4).

### Phase 3: The Deterministic Execution & Verification Harness
* Build an execution harness with strict sandboxing:
  - **Read/Search Tools**: Permitted locally without human review (iew_file, grep_search, list_dir).
  - **Patch Verification**: When Wrench emits an edit, the harness applies the patch to a temporary Git worktree and triggers the repository's deterministic tests (
pm test / pytest).
  - **The 1-Retry Rule**: If tests fail, feed the exact compiler/test failure string back to Wrench for at most **one** targeted correction turn.

### Phase 4: Self-Aware Competency & Escalation Classifier
The Wrench must not get trapped in hallucination loops. It must recognize its limits through dual criteria:
1. **Empirical Gate (Test Failure)**: If the patch fails after 1 retry -> trigger immediate escalation.
2. **Structural Complexity Gate**: If a task requires any of the following, abstain and route upstream immediately:
   - Modifications spanning > 3 decoupled files.
   - Database schema migrations / concurrency locking changes.
   - Cryptographic / authentication logic redesigns.
3. **Escalation Payload Packaging**:
   - The Wrench compresses the interaction into a structured JSON payload:
     - Target file & symbol.
     - Failing test assertion or compiler trace.
     - The candidate patch diff attempted by the Wrench.
     - Reason for escalation.
   - Forwards the payload directly to the teacher endpoint (http://127.0.0.1:4000/v1).

### Phase 5: Production Value & Economic Acceptance
* Measure production performance against a Teacher-Only control over identical frozen workloads:
  - **Token Savings**: >= 80% reduction in paid frontier tokens per accepted task.
  - **Zero Quality Loss**: Overall task pass rate on acceptance test suites must equal or exceed the teacher baseline.
  - **Latency Ceiling**: Gateway P99 latency overhead < 5 ms; local token generation > 100 tokens/sec.

---

## 4. Deliverables & File Mapping

| Artifact | Location | Purpose |
| :--- | :--- | :--- |
| **Project Plan** | PROJECT_PLAN.md | Master architectural specification and execution roadmap. |
| **Training Datasets** | dataset/ | Multi-turn tool calling, coding diffs, and schema enforcement JSONLs. |
| **Dataset Manifest** | manifest.json | Provenance, checksums, and dataset metadata. |
| **Execution Harness** | src/harness/ | Local test-gating, sandboxed tool runner, and escalation router. |
| **Trained Adapters** | weights/ | 4-bit LoRA adapter weights for the sub-4B base. |
