# Iteration 016: hourly resource and admission gate

Date: 2026-09-27 19:00 UTC (America/Edmonton)

Status: **NO TRAINING OR INFERENCE ADMITTED; CURRENT RAM IS BELOW THE FIT START GATE**

## Scope and current state

Wrench HEAD is `af01304824f079a64b6c3902397a2034b843511a`. This was a
read-only host/resource and automation check plus this bounded documentation
update. No training, inference, benchmark, provider request, download, or
service restart ran.

| Observation | Result |
| --- | --- |
| System RAM, 19:00 UTC | 4,052 / 32,702 MiB free (12.39%) |
| GPU | NVIDIA GeForce RTX 5060 Ti, 15,243 / 16,311 MiB free, 0% utilization |
| C: free space | 131.24 GiB |
| Process scan | No Python process command line matched `wrench`, `gateway`, `lora`, `transformers`, or `vllm` |
| Storage before this documentation reservation | `WITHIN_LIMIT`; 10,957,978,523 actual bytes plus 6,103,000 reserved bytes, including SubRoute |

The sample is above the general 10% runtime floor but only by 2.39 percentage
points. The current Qwen3.5-0.8B fit-03 protocol requires at least 25% free
RAM at process start, followed by at least 10% free RAM and VRAM during the
run. The start gate fails, so neither the fit nor a model load was started.
Unrelated applications and services were left untouched.

## Preparation-only diagnostic prerequisites

The local evidence-selection screen protocol remains marked **PREPARATION
ONLY. NO RUN AUTHORIZED**. Read-only path checks found its pinned local model
directory, runtime interpreter, and runtime lock. Its required
`local-evidence-selection-screen-01.admission.json` and
`local-evidence-selection-screen-01-model-inventory.json` are absent from
`C:\wrench-slm-data\artifacts\wrench-local-acceptability`. The protocol also
requires a separate exact-run authority record and root acceptance of the
fixture, runner, oracle, runtime identity, and manifest. This screen was not
run and no one-shot marker was created.

The 12-case mechanics screen would count local selected-evidence tokens and
validate evidence-ID selection/abstention. Its protocol explicitly says a
pass cannot establish repository coding acceptance, customer utility, or
frontier-token savings. It therefore remains a diagnostic preparation gate,
not a substitute for the paired LoRA effectiveness experiment.

## Hourly continuation state

The installed automation
`wrench-hourly-token-reduction-monitor` is `ACTIVE` with an hourly recurrence
and targets this thread. Its current prompt preserves the full goal, calls for
resource/storage/process rechecks, and directs one bounded contribution when
a gate blocks an experiment. The duplicate automation remains paused; no new
heartbeat was created.

The 100,000-byte reservation for this record and the matching goal update is
`WRENCH-HOURLY-RESOURCE-GATE-RECORD-20260927-01`. It remains active until
final status is checked and the files are accounted for.

## Next gate

Recheck RAM, VRAM, C: free space, and storage immediately before an admitted
job. Run fit 03 only after its exact-hash review, candidate/runtime checks,
unique storage reservation, disk-space requirement, and 25% free-RAM start
gate pass. Continue low-resource independent work while that gate is closed.
Keep the screen-01 diagnostic closed until its separate authority, root review,
current inventory, and admission manifest are all present. Keep the SubRoute
force route read-only until aggregate spend controls and call receipts are
authorized and verified.

The 95% local completion, 5% frontier routing, 95% frontier-token savings,
95% paired success retention, 95% all-in cost reduction, Wrench LoRA utility,
and day-long engineering remain unproven.
