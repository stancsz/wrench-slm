# Qwen3.5-2B screen-04 paired synthetic development evaluation

Status: exact-hash evaluation protocol for an inactive 2B adapter candidate.
This permits no run by itself. Require independent source/package review,
storage admission, and fresh hardware checks before each one-shot process.

## Question and comparison

Measure whether the completed, synthetic-only Qwen3.5-2B Wrench LoRA changes
bounded evidence-selection, retrieve/stop, compaction, and route decisions
versus the same frozen 2B base with its adapter disabled. The candidate is
inactive and receives no authority to execute tools or mutate code.

Both arms receive the same 64 prompt-only examples from the frozen development
projection used by Iteration 197. The scorer verifies and hashes the existing
prompt and oracle projection artifacts, appends the fixed output-schema
contract to a copy of each prompt in memory, and records the actual transformed
input hash. It runs deterministic decoding with at most 96 new tokens. The
model sees no labels. Raw predictions from both arms are flushed and hashed
before the scorer opens the separate oracle projection. It then computes exact
five-field decision accuracy, per-family results, schema validity, route
accuracy, and paired differences. Keep abstentions, invalid outputs, errors,
timeouts, and all 64 denominator rows in the report.

The reused projection artifacts retain their original Iteration 169 schema and
identity. Their reuse is intentional: this makes the 2B and Iteration 197 4B
arms comparable on exactly the same prompts and oracle. Do not regenerate,
edit, or expose the oracle before prediction sealing.

## Pinned candidate and score package

- Base: `Qwen/Qwen3.5-2B`, revision
  `15852e8c16360a2fea060d615a32b45270f8a8fc`; exact local inventory and config
  hashes are pinned in `tools/score_gateway_lora_screen_04_2b_dev.py`.
- Fit: `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-FIT-20260929-03`, exactly 96
  optimizer steps on 256 synthetic train examples; 64 synthetic dev examples
  were diagnostics only. The exact fit receipt, resource log, metrics, trainer,
  protocol, and inactive adapter files are hash-pinned by the scorer.
- Evaluator: `tools/score_gateway_lora_screen_04_2b_dev.py`.
- Runtime: the pinned Python 3.13.15 / Torch 2.14.0+cu132 / Transformers
  5.17.0 / PEFT 0.21.0 / Accelerate 1.15.0 runtime and RTX 5060 Ti identity.
- Source rows: the existing prompt-only and oracle-only projections; 64 unique
  IDs; the source dev split hash is fixed. No train row, held-out row, or
  provider response is used in scoring.

## One-shot gates

1. Review the exact current evaluator and protocol hashes. Check all output,
   scratch, log, and claim paths are absent. Inspect processes, fresh RAM/VRAM,
   GPU UUID, destination free space, and `check_wrench_storage_budget.py
   status`; create a unique reservation including every external Wrench root.
2. Run only `--mode preflight` with a unique
   `WRENCH-QWEN35-2B-DEV-PREFLIGHT-20260929-NN` job ID and at least
   500,000,000 reserved bytes. Preserve 10% free RAM and VRAM throughout and
   at least 5 GiB destination free space after the reservation. Both base and
   adapter-enabled outputs must finish under the cooperative generation cap
   and pass the fixed bounded-output validator. A failure stays sealed and
   blocks full scoring.
3. After preflight passes, independently review the exact score invocation,
   preflight receipt, all hashes, and fresh admission. Use a separate unique
   `WRENCH-QWEN35-2B-DEV-SCORE-20260929-NN` job ID and a separate reservation
   of at least 1,000,000,000 bytes. Run all 64 rows with the preflight receipt
   path explicitly supplied. The external hard timeout is four hours; a
   timeout is a failure, not a pass. Never duplicate a live job.
4. Keep the held-out split sealed. No Frontier, SubRoute, internet provider,
   credentials, spending, activation, or production routing is permitted.
   Release each reservation only after its process stops and all output bytes
   and hashes are accounted for.

The scorer requires at least 10% free system RAM and VRAM at start and during
the full workload, checks the pinned GPU identity, caps preflight scratch at
256 MiB and score scratch at 512 MiB, caps each output/log and aggregate output,
and records per-sample resource data. These are sampled safeguards, not an OS
quota. Report the exact resource minima and any monitoring gaps.

## Interpretation boundary

This is a synthetic development diagnostic, not a model-size winner, coding
agent evaluation, or product pass. It cannot prove 95% local task completion,
5% frontier escalation, 95% success retention, Frontier-token savings, all-in
cost, or all-day engineering. The local tokenizer counts only describe these
scoring prompts; actual Frontier usage and billing require provider usage
receipts in a separately authorized, capped experiment. Do not activate the
adapter based on this score.
