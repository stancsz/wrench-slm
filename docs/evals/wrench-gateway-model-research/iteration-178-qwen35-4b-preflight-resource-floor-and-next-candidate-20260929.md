# Iteration 178: 4B dev preflight resource-floor incident and candidate decision

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
No source, goal, model, adapter, route, or evaluation payload was changed.

## 4B preflight attempt 04

Job `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-04` passed its local identity and
prompt checks, started the pinned scorer, and began loading model weights. The
supervisor's resource log ends at 08:40:52 UTC with 8.37% free system RAM and
15,116 MiB free VRAM. The scorer stderr reached 59 of 723 tensors (about 8% of
weight loading) without a Python exception. At follow-up, neither the scorer
PID nor the supervisor PID existed. The supervisor status file remained stale
at `RUNNING` with its last heartbeat at 08:40:47 UTC. The output directory was
present but contained no files; stdout was empty. No prediction, completed
preflight receipt, model-quality score, or provider call was produced.

This is a **resource-floor failure with incomplete supervisor close-out**. It
is neither a model-quality result nor evidence that 4B cannot run on this
machine: the same hardware previously completed the three-case 4B base-model
screen and a 96-step 4B LoRA fit, both above their sampled 10% floors. It also
does not prove the dev scorer is safe to retry unchanged. The exact cause of
both processes disappearing is unresolved.

The reviewed scorer currently constructs the BF16 model on CPU and then moves
it to CUDA (`tools/score_gateway_lora_screen_03_4b_dev.py`, `prepare_model`).
This makes CPU-side load-time memory a concrete optimization hypothesis. A
direct-to-GPU load may reduce host-RAM peak, but it has not been tested and
must preserve the reviewed base/adapter composition, pinned runtime, and VRAM
reserve. A later candidate run needs a new job ID, fresh >=10% admission with
adequate measured headroom, a supervisor that survives child termination and
records a terminal receipt, and a bounded output inventory. Do not reuse
attempt 04.

## Candidate ranking from existing evidence

| Candidate | Evidence relevant to the next controller evaluation | Limitation | Next role |
|---|---|---|---|
| Qwen3.5-4B + existing Wrench LoRA | Only 4B passed all 3 known answers in the Iteration 158 related-TOML-table arm. Its separate synthetic fit completed 96 steps with 1,572,864 trainable LoRA parameters and minimum sampled RAM/VRAM of 17.13%/16.76%. | Table arm is a reused three-case base-model result. The adapter has no quality evaluation. Attempt 04 hit 8.37% free RAM before inference. | Lead candidate for the next safe base-vs-LoRA dev comparison, after fixing load/supervisor admission. |
| Qwen3.5-2B | Same three-case related-path arm passed 3/3. It loaded faster and used less VRAM than 4B; its minimum sampled RAM was 12.13%. | Related-table arm passed only 2/3, and the target-token prompt reduction was 94.937%. No Wrench LoRA fit/evaluation. | Lower-resource challenger; switch here if 4B cannot sustain the hard resource floor. |
| Qwen3.5-0.8B | Smallest control and has prior bounded hardware runs. | Iteration 155 passed 2/3 versus 3/3 for 2B on the same known battery. | Control, not current lead. |

The model-size evidence supports **4B as the next experiment**, with moderate
confidence in that priority and low confidence in any product-wide size winner.
This does not establish broad coding, the 95% local completion rate, the 5%
frontier route rate, success retention, all-day use, or frontier-token/cost
savings. The 94.937% and 97.860% figures in Iteration 158 refer respectively
to a target-tokenizer context proxy and local-model token counts. The run made
zero Frontier calls, so billed Frontier savings remain unavailable.

## Accounting and handoff

- Attempt 04 had a unique 500,000,000-byte reservation with the external WSL
  Docker model volume, automation directory, worktrees, and approved data
  root included. It was released after confirming there was no live process
  and counting the empty scorer output directory and bounded logs.
- The final storage status was `WITHIN_LIMIT`: 29,290,696,131 actual bytes
  plus 6,103,000 bytes of existing reservations, below the 50 GB limit.
- At final inspection, RAM was 30.26% free and GPU memory was 15,210/16,311 MiB
  free. These are snapshots and do not admit the next workload.
- No inference, training, benchmark, test, held-out access, route change,
  credential access, or network request occurred in this incident review.

References: [Iteration 158](iteration-158-common-battery-qwen2b-vs-4b-20260928.md),
[Iteration 166](iteration-166-qwen35-4b-fit-01-20260929.md), and
[Iteration 177](iteration-177-qwen35-4b-dev-preflight-interrupted-during-torch-import-20260929.md).
