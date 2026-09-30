# Wrench gateway LoRA screen 01 protocol

Status: preregistration frozen before training; synthetic splits generated; training not run
Date: 2026-09-27 (America/Edmonton)
Goal: [gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)
Readiness: [iteration 000](iteration-000-readiness-20260927.md)

## Objective and scope

Test whether LoRA improves a small model's **bounded Wrench decisions** over
the same frozen model and a deterministic policy. It does not test whether the
model can independently perform broad software engineering. Exact retrieval,
source integrity, budget enforcement, parsing, tool execution and verification
remain deterministic.

This protocol covers synthetic development and a local adapter candidate. It
does not authorize a model download, external generation call, client request,
real-task capture/transfer, production routing, or activation of the candidate.

## Frozen candidate

- Model: `Qwen/Qwen3.5-0.8B`
- Revision: `2fc06364715b967f1860aea9cf38778875588b17`
- Existing snapshot: `C:\wrench-slm-data\weights\Qwen3.5-0.8B`
- Prior full inventory: 13 files, 1,769,980,465 bytes; historical manifest is
  [candidate metadata](../../northstar/model-candidate.json). A fresh 13-file
  size/SHA-256 inventory is mandatory before any run.
- Runtime starting point: Python 3.13.15, Transformers 5.17.0,
  Torch 2.14.0+cu132. PEFT, trainer dependencies, model module matches, CUDA
  dtype, and exact save/load support remain to be proven.
- Foundation and any installed Wrench-Core adapter are read-only. Save only
  one new candidate adapter, one compact receipt, and bounded logs under
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-01`.

## Data plan

Create new synthetic scenarios with no source from old Wrench evaluations,
repository code, customer traces, public benchmarks, or a teacher model. A
small deterministic generator must emit separate immutable train, development,
and held-out evaluation files before training. Plan for 256 train, 64 dev, and
128 held-out examples across four families: known-ID evidence selection,
retrieve/stop/abstain, context-preservation/compaction policy, and local versus
frontier routing. Split by template family and scenario composition, not random
rows. No paraphrase, lineage, or seed value may cross splits. Record generator
source/hash, seed, every file hash, task-family IDs, and exact counts.

The generator labels are a synthetic policy oracle, not real outcome evidence.
Keep the held-out file sealed from training and hyperparameter selection. If it
is accidentally inspected during tuning, retire it and author a fresh split.
Do not use the ten-case seed or any exposed local-acceptability result.

Generation completed under storage job
`WRENCH-GATEWAY-LORA-SCREEN-01-DATA-20260927`; the hash-bound split identity
and counts are recorded in [iteration 001](iteration-001-dataset-prep-20260927.md).
The held-out JSONL has not been opened for scoring or tuning.

## Output contract and authority

The model proposes only:

- `route`: `LOCAL_MECHANICAL`, `LOCAL_COMPACTION`, `FRONTIER`, or `ABSTAIN`;
- `operation`: a fixed reviewed enum such as `EXACT_RETRIEVE`, `COMPACT`, or
  `NOOP`;
- `selected_evidence_ids`: zero or more IDs present in the input;
- `retrieve_more`: boolean;
- `reason_code`: one short enum, never free-form authority text.

The parser rejects unknown keys, invalid enums, duplicate IDs, missing IDs,
or over-budget selections. The runtime owns all permissions and action
execution. A frontier decision only asks the host to route; it cannot itself
call the provider.

## Training plan

Use one adapter, no foundation fine-tune and no adapter activation. Initial
settings: rank 8, alpha 16, dropout 0.05, batch size 1, gradient accumulation
8, maximum sequence 512 tokens, maximum 3 epochs/96 optimizer steps, no saved
intermediate checkpoints, and no more than one final adapter. Disable KV
cache; use gradient checkpointing if supported. Verify the exact LoRA target
module allowlist from the pinned model key/module inventory before training.
The current checkpoint key inventory includes the text projections `q_proj`,
`k_proj`, `v_proj`, `o_proj`, `in_proj_qkv`, `in_proj_z`, `in_proj_a`,
`in_proj_b`, `out_proj`, `gate_proj`, `up_proj`, and `down_proj`; confirm these
names against instantiated modules and freeze the actual matched list before
the first optimizer step. Exclude vision-only modules.

The learning rate, optimizer, precision, package versions, seed, stopping
rule, and output byte limits must be added to the run manifest before training.
For this screen, freeze them as follows: AdamW, learning rate `2e-4`,
weight decay `0`, gradient norm cap `1.0`, FP32, CPU execution on the available
AVX2 host, seed `20260927`, exactly 3 epochs (96 optimizer steps), no early
stopping, and no intermediate checkpoints. Development loss is diagnostic
only and will not select a checkpoint. Cap the final adapter at 100 MB and
the combined run/resource logs at 20 MB. Record the exact package versions
and module names in the run manifest before the first optimizer step. Do not
choose settings after reading held-out results. If no tested compatible
adapter implementation works without breaching resource reserves, record
`BLOCKED_RESOURCE_OR_COMPATIBILITY` and stop. A one-step preflight must hold at
least 10% of system RAM and VRAM free throughout; at the 2026-09-27 sample only
about 3,452 MiB of VRAM was available above the reserve, which has not been
shown sufficient.

Before the preflight and again before full training: run storage `status`,
reserve the measured aggregate peak with a unique job ID, include all Wrench
roots, check C: free space, set `HF_HOME` and `TORCH_HOME` under
`C:\wrench-slm-data`, record resource samples, and retain no intermediate
checkpoints. Release the reservation only after the process stops and final
files are accounted for.

## Arms and metrics

Run the same frozen held-out inputs through:

1. Deterministic policy baseline.
2. Base Qwen3.5-0.8B without Wrench LoRA.
3. Base plus the new LoRA.

Record each case, exact prompt/tokenizer/template/model/adapter hashes, raw
bounded output, parser result, route/action match, chosen IDs, exact-source
coverage, over-budget error, invalid-ID error, false escalation and resource
cost. Preserve all failures in the denominator. Report exact counts and
per-family results; calculate paired uncertainty. Primary local metric is
held-out exact valid decision accuracy. Safety gate is zero invalid-source
acceptances and zero authority violations. A diagnostic screen passing a 95%
point estimate is **not** a 95% confidence claim or production acceptance.

For context policy, report input-token reduction only after all selected source
IDs are resolved against the exact snapshot. Record omission rate, critical
evidence recall, hot-context preservation, and re-fetch success. Do not score a
summary for brevity alone.

## Strong-model comparison and cost

The user requested the subroute at `http://127.0.0.1:4000`. The latest read-only
route snapshot showed force-mode OpenRouter; any prompt can incur usage charges.
No generation call may occur until the user gives a USD cap and the run pins
the actual active provider/model, force-mode behavior, task list, provider
usage receipt method, retry limits, and reference tokenizer. A model alias or
`/v1/models` response is insufficient.

Once separately admitted, compare the same synthetic held-out task set on
direct strong model alone, deterministic Wrench plus that model, and
LoRA-gateway plus the same model. Count all retries, fallbacks, verification,
input/output usage, actual invoice amounts, local GPU/CPU energy, training
cost, and failure outcomes. Report task-value retention, task pass rate,
all-in cost ratio, frontier-token ratio, route share, latency and resource use.
The local synthetic comparison is only infrastructure/behavior evidence. No
95/95 product claim follows without adequately powered, consented,
outcome-verified real engineering tasks and the sustained-work study.

## Abort conditions

Abort before or during the run if the candidate or tokenizer hash changes,
the data split cannot be verified, module targets are missing, the adapter
cannot round-trip, any authority gate fails, any storage reservation is
incomplete, C: or the aggregate ceiling is endangered, 10% RAM/VRAM is
breached, the output schema admits a nonexistent source ID, the provider route
is not pinned, or an external spend/usage cap is unavailable. Preserve failed
receipts and do not recycle them into training.
