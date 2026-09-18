# Project Plan: Wrench SLM (<4B) - Distillation, Selective Offload & Escalation

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
  revision `995ad96eacd98c81ed38be0c5b274b04031597b0`; 71.9 GB of unquantized
  safetensors are still absent locally.
- **Phase 4, task portfolio:** proposed family-disjoint scope is frozen in
  `phases/phase-4-task-portfolio/portfolio.json`; human approval is pending.
- **Phase 6, runtime compatibility:** the current global Transformers 4.57.1
  cannot load the Qwen3.6 architecture. A project-scoped requirement and
  non-mutating check report global `NOT_READY`; an isolated Transformers 5.17.0
  environment with the existing PyTorch reports runtime `READY` without loading
  weights. Meta-tensor instantiation of `Qwen3_5MoeForConditionalGeneration`
  also passes; actual weight loading and GPU execution remain unverified.
- **Next gate:** authorize acquisition of the unquantized source, verify it
  against the official index, install and verify the project runtime, obtain
  portfolio approval, and only then begin router profiling.

## 1. Executive Summary & Core Objective

The objective of **Wrench SLM** is to build a high-velocity, sub-4-billion parameter local model specialized in developer-tool workflows, repository navigation, noise compaction, and deterministic code repair. 

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
                 │             WRENCH SLM (< 4B)                 │
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
