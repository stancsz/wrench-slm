# Wrench gateway LoRA screen 04 attempt 02: Qwen3.5-2B

Attempt 01 stopped safely before model loading because the model directory
contained Hugging Face .cache metadata outside the pinned 13-file model
inventory. The 3,474 metadata bytes were preserved under
C:\wrench-slm-data\cache\hf-snapshot-metadata\Qwen3.5-2B\.cache; the model
files were not changed. Attempt 02 uses fresh one-shot preflight and fit identities.

# Wrench gateway LoRA screen 04: Qwen3.5-2B GPU protocol

Status: **Package prepared for independent exact-hash review only. Nothing in
this protocol or trainer authorizes execution. Preflight attempt 01 failed
safely before model loading; no fit, evaluation, adapter activation, production
routing, or spending has occurred.** The synthetic screen can check execution
mechanics and bounded update behavior. It cannot establish Wrench task quality,
repository engineering ability, all-day work, or the 95/5/95 product target.

## Scope and pinned inputs

- Base: `Qwen/Qwen3.5-2B`, revision
  `15852e8c16360a2fea060d615a32b45270f8a8fc`, local snapshot
  `C:\wrench-slm-data\weights\Qwen3.5-2B`, 13 files / 4,571,274,023 bytes.
  License: Apache-2.0. Inventory SHA-256
  `23E0D5F79E57D41AB9F007B697D8F75F56F5F528519BFDF15F406E1F28DF3DD5`;
  independent candidate-manifest SHA-256
  `D4917EF337978B93D2220A9888CB4F640EDB63E54C8E49F70F0696B175DD2956`.
- `config.json` SHA-256
  `ED1C1723241F23F7F4E23430759CBD7DCFB4103CBDFE052BFE7626B57C2615B4`;
  `model.safetensors.index.json` SHA-256
  `ACA8AFED9DA75B0F050B408D270766FD77627F1AF401E240F61C3B47D0DB02F9`;
  `LICENSE` SHA-256
  `BBEDC3FDA3305820B977265F01B8619D87570A6739DE3A5582C3464840F1E57A`.
  The runner checks these files independently, then pins and verifies the
  complete model tree while the Transformers loader reads it.
- Dataset: the existing synthetic screen-01 split only. Manifest SHA-256
  `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED`;
  train: 256 rows, 375,968 bytes, SHA-256
  `22F45C8B51EF680F9D05E8C42243EBB34E9F596B22D76577C64E371D272A39D2`;
  dev: 64 rows, 93,743 bytes, SHA-256
  `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7`.
  The runner reads each split once through a confined handle and parses those
  same verified bytes. It never opens, lists, hashes, or reads the sealed
  `heldout.jsonl` payload.
- Runtime pins: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0,
  PEFT 0.21.0, Accelerate 1.15.0. Use only the existing local interpreter and
  add-on directory named in the trainer. Offline mode and telemetry disablement
  are enforced before loading. No package installation or network access.
- GPU identity is pinned to the observed RTX 5060 Ti, UUID
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. The current receipt must still
  pass exact runtime device checks; prior host samples are not run admission.

## Adapter and fixed workload

The config gate requires the Qwen3.5 text model, 24 text layers, hidden size
2048, 8 attention heads, 2 KV heads, head dimension 256, BF16 dtype, and the
exact layer schedule with full attention at `[3, 7, 11, 15, 19, 23]` and linear
attention elsewhere. The vision configuration is present but excluded.

The sole profile is rank-8 LoRA, alpha 16, dropout 0.05, no bias, on exactly
`model.language_model.layers.{3,7,11,15,19,23}.self_attn.{q_proj,k_proj,v_proj,o_proj}`.
The runner discovers these names from the instantiated model, requires every
target to be a linear layer with dimensions derived from the pinned config,
rejects unexpected projection candidates, and verifies that only LoRA
parameters are trainable and no vision parameter is trainable. The config
dimensions imply 638,976 LoRA parameters; the runner recomputes this count and
requires the instantiated count to match. The preflight receipt records actual
module names and actual trainable count; fit must match both exactly.

The frozen foundation is loaded in BF16 on the pinned GPU. The installed
Wrench-Core adapter is not loaded or modified. Synthetic labels use the
existing four families: evidence selection, retrieve/stop, compaction policy,
and route. Batch size is one, max sequence length 512, gradient accumulation
8, AdamW learning rate `2e-4`, zero weight decay, gradient norm cap 1.0, seed
`20260927`, and three epochs. A full fit must complete exactly 96 optimizer
steps. The separate one-step preflight uses only the first eight training
examples and saves no adapter. Dev loss is diagnostic only; it does not choose
checkpoints or tune the run. Non-finite loss, gradient, or updated trainable
parameter aborts the run.

## One-shot run identities and paths

Preflight identity: `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-PREFLIGHT-20260929-02`.
Receipt and resource log root:
`C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-04-qwen35-2b-preflight-02`.
Scratch and exclusive claim paths use that full job ID below their screen-04
cache roots.

Fit identity: `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-FIT-20260929-02`.
Candidate root:
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-04-qwen35-2b\fit-02`.
Logs:
`C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-04-qwen35-2b-fit-02`.
Only the adapter is promoted from bounded staging, with a no-replace rename.
The exact trainer source is copied into the fit artifact root. Adapter output
is capped at 100 MB; each receipt/resource/metric log at 20 MB; runtime scratch
is capped at 256 MiB for preflight and 512 MiB for fit. The destination volume
must have the active reservation plus at least 5 GiB free. The runner refuses
all existing output, scratch, and per-job claim paths, and claims each ID
durably before creating the run receipt. Failed IDs and paths are never reused.

## Admission and resource limits

1. Before each separate job, inspect live RAM, VRAM, processes, and output
   paths; run the storage checker and obtain a fresh reservation for that
   exact run ID, including all external Wrench roots. Preflight requires at
   least 250,000,000 reserved bytes. Fit requires at least 2,000,000,000
   reserved bytes. Reservations do not include permission to exceed the
   aggregate 50 GB Wrench storage ceiling. Do not launch if reservation or
   5 GiB destination headroom is unavailable.
2. After exact-hash source review, run only the one-shot preflight with the
   pinned interpreter, explicit `--preflight-only`, exact profile, and exact
   preflight reservation ID. Start must have at least 10% free RAM and VRAM;
   both floors apply throughout. Require its successful receipt and resource
   log to bind the trainer, protocol, model revision and all model hashes,
   data manifest/train/dev hashes, device UUID, runtime package identities,
   chat template, exact target names/count, trainable count, storage
   reservation, scratch cap, and complete resource samples. Release the
   stopped preflight reservation only after accounting for its files.
3. Obtain a separate fit reservation and repeat live resource and disk checks.
   Fit admission requires at least 25% free system RAM at process start and
   at least 10% free RAM and VRAM throughout. Fit reads the preflight manifest
   and resource log through confined handles, checks their hashes and terminal
   status, requires the preflight reservation released, and compares the full
   source/model/data/runtime/device/adapter identity. It uses the same unique
   fit ID in the reservation, claim, output, and logs.
4. Resource monitor samples RAM, VRAM, GPU identity, and scratch about once per
   second from before heavyweight imports and model/data loading. It interrupts
   on a floor, scratch, GPU identity, or log-size breach. Every optimizer
   boundary rechecks the active reservation and monitor state. A terminal
   success is accepted only after final resource log hashing, floor validation,
   scratch accounting, and final receipt update. Failure leaves a terminal
   failed/aborted receipt and cannot promote an adapter.
5. Keep the candidate inactive. This runner has no activation or routing
   interface. Preserve the exact output and receipt; do not treat a successful
   synthetic fit as an approved adapter or production component.

At preparation time the live sample was about 29.96% free RAM (9.57 GiB) and
15,196 MiB free VRAM of 16,311 MiB. These are informational preparation
samples only, not authorization or admission for either future job. A future
job must inspect live resources again. The storage checker is admission, not
an OS quota or automatic kill switch; resource monitoring is sampled and does
not guarantee zero latency before interruption.

## Interpretation and next evaluation

This package tests whether the pinned 2B BF16 model can load, expose the exact
full-attention targets, execute one bounded update, and complete a fixed
synthetic fit while preserving resource and storage controls. It does not prove
that a LoRA improves context compression, tool choice, repository task quality,
engineering throughput, sustained all-day work, or robustness. Synthetic
passes and token reduction alone do not establish downstream task success.

The product acceptance target remains: Wrench must deliver at least 95% of the
strong-model-alone completed-task value, route at most 5% of episodes to the
frontier, and use at most 5% of frontier tokens and all-in cost, including
router, retries, and local compute. The next decisive work is an independently
reviewed, outcome-backed evaluation on consented, non-sealed repository tasks:
compare strong-model-alone, Wrench plus frontier fallback, and the same system
with the trained adapter inactive/active under a fixed routing policy; report
task-level success, regressions, intervention rate, frontier episodes/tokens,
total cost, latency, and a multi-hour sustained engineering run. Keep sealed
final data quarantined until the training/evaluation plan is frozen and
separately authorized.

