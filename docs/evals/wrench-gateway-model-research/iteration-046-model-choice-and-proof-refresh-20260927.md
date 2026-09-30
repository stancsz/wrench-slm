# Iteration 046: model choice and evidence refresh (2026-09-27)

## Decision

For the next coding-worker fit preflight, prioritize the pinned Qwen3.5-4B
candidate. Keep the Qwen2.5-Coder-7B as a specialist challenger if the 4B
misses a preregistered repository-task gate. Keep the Wrench controller LoRA
separate: first test the already staged Qwen3.5-0.8B finite-action policy,
then consider Qwen3.5-2B only if the 0.8B LoRA has a measured capacity error.

This is role-specific research selection for the next preflight, not a winner
or a model-run authorization. It preserves the user's requirement to train a
Wrench-specific LoRA while avoiding the unsupported assumption that the same
small controller is already a reliable software engineer.

## New and reconciled evidence

- Reconfirmed the complete 14-file Qwen3.5-4B tree at revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, totaling 9,342,907,469 bytes.
  The pinned tree includes two weight shards of 5,329,398,688 and
  3,990,429,408 bytes, with their SHA-256 hashes in the linked report.
- The Qwen3.5-4B model card reports LiveCodeBench v6 55.8, BFCL-V4 50.3,
  and TAU2-Bench 79.9. Unsloth's current guide estimates around 10 GB for
  BF16 LoRA and warns against QLoRA for Qwen3.5. These are published
  compatibility/capability signals, not host measurements or Wrench results.
- Compared with the already inventoried 7.61B code-specific Qwen2.5-Coder,
  4B needs less weight storage and stays in the Qwen3.5 family already used by
  the Wrench runtime. The 7B remains attractive as a code-specialist
  challenger, but it needs a new causal-model QLoRA runner, bitsandbytes
  package admission, exact target mapping, and its own monitored preflight.
- Latest resource sample: 7.98% system RAM free. This is below the 10% floor
  and the 25% training start gate. No runtime job was admitted.
- SubRoute `http://127.0.0.1:4000` passed read-only liveness GET and listed
  19 aliases. No POST, provider generation, or spend occurred. A numeric
  aggregate cap and validated durable caller-side billing/usage receipts are
  still required for a paid arm.

## Reliability and claim status

The 0/10 result belongs to the unadapted 0.8B semantic screen. The one-step
attention-only optimizer preflight establishes compatibility, not learning or
held-out performance. The small synthetic split's 81.25% LOCAL, 6.25%
FRONTIER, and 12.5% ABSTAIN composition cannot meet the 95%/5% targets even
with a perfect classifier. The earlier 12.1% context reduction does not
measure complete frontier usage, task completion, or all-in cost.

Thus the general-controller direction is not supported by current evidence;
the narrower deterministic mechanics plus reviewed Wrench-LoRA policy remains
testable. No current result demonstrates 95% local task completion, 95%
frontier-token savings, 95% lower all-in cost, or all-day engineering. The
candidate comparison and paired proof plan are in the
[decision report](../../reports/wrench-gateway-model-research/model-choice-and-proof-plan-20260927.md).

## Work and storage

- Only research documentation and the live goal log were updated.
- No model was downloaded, loaded, selected for deployment, or run. No
  package was installed. No tests, training, inference, benchmark, or
  delegation ran. No provider POST or spend occurred.
- Storage status included `C:\Users\stanc\github\subroute` and was
  `WITHIN_LIMIT`: 10,992,599,173 actual bytes and 8,103,000 existing
  reservation bytes before this job. Documentation reservation:
  `WRENCH-MODEL-DECISION-RESEARCH-20260927-01`, 500,000 bytes.

