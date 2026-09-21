# Working agreement: Wrench 多快好省 Production-Ready Execution

Write naturally. Do not use em dashes.

## Core Objective and Production Target

The single delivery target of this repository is **one smallest-sufficient production-ready Wrench SLM**. The former 4.25B figure is a ceiling, not the objective. Choose the smallest candidate that delivers broad verified mechanical coverage, lower latency, preserved final success and safety, and at least 95% net frontier-token savings.

The model operates as a bounded, specialized developer-tool execution SLM and fast defensive gatekeeper:
1. **Eligible Routine Tools**: Offload at least 90% of the weighted mechanical-workload frontier-token mass for routine, verifiable developer-tool tasks (`read_file`, `read_lines`, `literal_search`, `git_read_status`, `health_read`, `patch_draft`).
2. **Deterministic Abstention and Clean Escalation**: Confidently identify out-of-boundary, risky, complex, or multi-step tasks, emitting structured `abstain` outcomes so the harness cleanly routes requests to the smarter frontier model without corrupting context or materially regressing final success.
3. **No Direct Mutation Authority**: Wrench proposes bounded structured actions or abstains. It never executes arbitrary shell commands, accesses credentials, or writes autonomously.

## Ownership and Completion Gates

All engineering, training, calibration, and evaluation must directly target the release gates defined in `docs/WRENCH_4B_PRODUCTION_UTILITY_TEST_CONTRACT.md`:

- **Gate A (Proposal Semantics)**: Zero schema errors. Eligible cases match typed oracles; out-of-boundary cases match exact expected abstention reasons.
- **Gate B (Verifier & Authority Bounds)**: Strict zero tolerance for prohibited accepts (0 Prohibited Accepts). Any unexpected side effect or unverified boundary escape is an immediate `FAIL_WRENCH`.
- **Gate C (Model Comparison vs. Full-Expert Teacher)**:
  - Final task success and safety must not materially regress against the teacher-only workflow. Report eligible-task correct acceptance and overall correct outcomes with paired 95% confidence intervals.
  - Median and p95 end-to-end latency must improve by >= 50% on successful eligible tasks (fast refusals do not count as fast completion).
- **Gate D (Matched Real-Workflow Utility - Three-Arm Replay)**:
  - Replay matched traces across: (1) Stronger model only, (2) Rules + fallback, (3) Wrench + fallback.
  - Cover at least 90% of weighted mechanical-workload frontier-token mass and deliver at least 95% net frontier-token savings (accounting for local inference, verification, compaction, retries, corrections, and fallback overhead) with zero material final-success regression.
- **Gate E (Operational & Operational Shadow)**: Robust under concurrency, cancellation, timeout, and circuit breaking via `ProposalRouter`.

## Training and Iteration Guidelines

When preparing training data, calibrations, or model weights:
1. **Dataset Discipline**:
   - Ensure a balanced mix: include high-quality positive routine developer-tool traces AND explicit negative / out-of-scope tasks teaching decisive `abstain`.
   - Never allow training or tuning on the sealed evaluation split (`final.jsonl`).
2. **Local Worker Coordination**:
   - Follow `AGENTS.local.md` when delegating batch runs or heavy training jobs to the 5060TI worker via the job queue.
   - Separate interactive 5070Ti measurements from independent 5060TI verification.
3. **Evidence Over Assumptions**:
   - Never equate prompt tweaks, synthetic fixture passes, or parameter count with production utility.
   - Record verifiable receipts (hash-bound checkpoints, latency distributions, exact failure logs) under `phases/` before claiming progress.

## Host Resource Safety

Every training, inference, benchmark, packaging, and delegated worker job must preserve normal host operation:

- Keep at least 10% of total host system memory free at all times.
- Keep at least 10% of total host VRAM free at all times.
- Check available memory and VRAM before starting work and during long-running work. If either reserve would be breached, reduce concurrency, batch size, context size, cache size, or model footprint before continuing.
- Prefer releasing framework caches and lowering workload intensity. Do not terminate unrelated applications, Docker services, or WSL distributions without explicit user authorization.
- A job that cannot maintain both 10% reserves is resource-unsafe and must be paused or marked failed, not treated as a valid benchmark result.

## Complete Delegated Worker Payload

Every message or job sent to a remote worker must be self-contained. It must
repeat the unique nonce and job ID, the full objective and verification scope,
the repository and expected commit, the artifact or package identity and
hashes, exact allowed commands and output paths, timeout and retry limits, the
10% RAM and VRAM reserve, explicit no-spend and no-credential boundaries, and
the complete final response schema. The worker must not need conversation
history or an implicit plan.

An empty turn, missing nonce, missing required fields, or execution on the
wrong host is unverified. Start a fresh authenticated worker session instead
of appending more context to the failed thread. Never promote such a result to
independent hardware, benchmark, parity, or release evidence.
