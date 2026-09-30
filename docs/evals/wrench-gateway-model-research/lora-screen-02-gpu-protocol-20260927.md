# Wrench gateway LoRA screen 02: GPU fit protocol

Status: **Historical assignment 29 and attention-only preflight 04 remain
compatibility evidence only. A fresh attention-only preflight 05 and fit 03
path is now implemented and awaiting exact-hash review. No fit is admitted
until that review passes, preflight 05 passes, and live RAM is at least 25% at
fit start. No adapter, quality, engineering-effectiveness, or 95/5/95 result
exists.**

Historical sections below that name preflight 03/04, fit 01/02, or their
reservations and paths describe those immutable attempts only. They are
superseded for current execution by the latest dated section at the end of
this protocol. The runner rejects their old identities.

## Reason for a new screen

Screen 01's frozen CPU/FP32 fit terminated before its first optimizer step.
Its last resource sample recorded 9.72% free system RAM, below the required
10% reserve. Python 3.13 lacks `threading.interrupt_main`; that runner bug
masked the resource breach as an `AttributeError`. The failed run produced no
adapter and its reservation is released. Screen 01 is a failed fit, not a
model-quality result.

Screen 02 keeps the same pinned Qwen3.5-0.8B base, synthetic-only train/dev
split, labels, LoRA targets and hyperparameters, but runs on the currently
observed RTX 5060 Ti in FP32. This is a distinct run with distinct artifact
paths and hashes. The GPU sample at 2026-09-27 09:43 UTC showed 16,311 MiB
total and 15,193 MiB free. It is an idle snapshot, not proof the fit will fit.
The frozen foundation, installed Core adapter, sealed split, and production
configuration remain untouched.

## Fixed run contract

- Model: `Qwen/Qwen3.5-0.8B`, pinned revision
  `2fc06364715b967f1860aea9cf38778875588b17`, from the verified local snapshot
  only. No download or alias resolution.
- Model inventory SHA-256:
  `64C38776F5D208C666E7033A0E121A63A240538F1F55B8865B5D31FDDC474519`.
  Independently pinned candidate metadata SHA-256:
  `6CEFDBBD0203D8E78EB1DEE655E82C65EFCFA425B57A80CB335242645F47F0A9`.
- Data: existing synthetic-only screen-01 train/dev split (256/64 rows).
  Read and hash train/dev; never open heldout during fit or preflight.
- Dataset manifest SHA-256:
  `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED`.
  Train SHA-256:
  `22F45C8B51EF680F9D05E8C42243EBB34E9F596B22D76577C64E371D272A39D2`.
  Dev SHA-256:
  `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7`.
- Device and precision: `cuda:0`, FP32, with `device_map` pinned to the single
  GPU. Require the sole visible device to be NVIDIA GeForce RTX 5060 Ti,
  index 0, UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`; pin
  `CUDA_VISIBLE_DEVICES` to that UUID. Record device identity, CUDA, PyTorch
  and package versions in the receipt. If the GPU is unavailable or any module
  is off-device, fail closed.
- Adapter: rank 8, alpha 16, dropout 0.05, no bias, the exact allowlisted text
  projection modules verified against the instantiated model; no vision-only
  modules.
- Optimizer: AdamW, learning rate `2e-4`, weight decay `0`, gradient norm cap
  `1.0`, gradient accumulation 8, batch size 1, sequence cap 512, seed
  `20260927`, exactly 3 epochs and 96 optimizer steps. No early stopping or
  intermediate checkpoints. Dev loss is diagnostic only.
- Output: one candidate adapter at most 100 MB, no activation, plus bounded
  receipts/logs at most 20 MB. The runner copies its exact source to the
  approved artifact root and records that hash.
- Runtime: use the existing approved interpreter
  `C:\\wrench-slm-data\\envs\\wrench-local-synthetic-cp313\\Scripts\\python.exe`
  (Python 3.13.15, torch 2.14.0+cu132, transformers 5.17.0) with
  `WRENCH_LORA_ADDONS` set to
  `C:\\wrench-slm-data\\envs\\wrench-gateway-lora-screen-01-addons`
  (PEFT 0.21.0, Accelerate 1.15.0). These existing local packages are recorded
  in each receipt; do not install or download dependencies for this screen.
  Before creating artifacts, the runner requires `sys.executable` to resolve
  to that exact interpreter, Python version 3.13.15, and `WRENCH_LORA_ADDONS` to
  resolve to that exact directory. After import and before model/data loading,
  it enforces the pinned Torch, Transformers, PEFT and Accelerate versions and
  verifies Torch/Transformers originate inside the approved interpreter while
  PEFT/Accelerate originate inside the pinned add-on directory. The manifest
  records those paths and versions. Fit compares the complete runtime identity
  with attempt-03's preflight receipt. Launch with `WRENCH_LORA_ADDONS` set to
  that exact directory and invoke the exact interpreter above with `-B`; do
  not use the unrelated AppData `python` command.
  Preflight attempt 01 used the unconfigured AppData Python and failed at
  `import torch` before model, dataset, or held-out reads. Preserve that failed
  receipt and do not reuse its job ID, log path, or scratch path.
- The next one-step preflight has job ID
  `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-03`, log directory
  `C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-preflight-03`,
  and a distinct per-job scratch path. The full fit job ID is
  `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-02`; it writes only under
  `C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\lora-screen-02\\fit-02`
  with a separate `lora-screen-02-fit-02` log directory. It may consume only
  attempt 03's successful, hash-matched receipt. Attempt 02 preflight and fit
  attempt 01 outputs remain immutable.
- Scratch: use a new per-job directory under
  `C:\\wrench-slm-data\\cache\\gateway-lora-screen-02\\<job-id>`. Route
  Hugging Face, Torch, XDG, CUDA, Triton, extension-build, and OS temporary
  paths there; run offline with telemetry disabled. The preflight scratch cap
  is 128 MiB and its reservation is at least 250,000,000 bytes. The full-fit
  scratch cap is 512 MiB and its reservation is at least 750,000,000 bytes.
  Record scratch bytes in each resource sample and the finalized receipt; stop
  on a sampled cap breach and reject success if final accounting exceeds the
  cap. This is application-level monitoring, not an OS quota, so the approved
  storage reservation still covers simultaneous output and temporary growth.
- Resource monitor: sample RAM and VRAM throughout; hard floor is 10% free for
  each. Start before heavyweight imports and model/data loading. Use
  `_thread.interrupt_main()` on a breach and preserve the exact reason. Stop
  immediately if either floor is crossed. Check every sample's GPU identity
  and both floors again before recording success. The full-fit runner also
  requires at least 25% RAM free before it creates artifacts; it records the
  observed start fraction and threshold in the fit manifest. This operating
  buffer follows fit attempt 01, which started at 16.70% and crossed the 10%
  hard floor during its 34.7-second startup/load. The one-step preflight keeps
  the 10% hard floor and its monitored resource receipt.
- Data paths from the manifest must be relative and resolve inside the pinned
  dataset root. The trainer pins the manifest, train/dev files, model inventory,
  candidate metadata, and visible GPU identity independently. Before reading
  Wrench-owned inputs, resolve the dataset root, model root, inventory, and
  reservation through junctions/symlinks and require the resolved paths to
  remain under `C:\\wrench-slm-data`.
- Read the dataset manifest, model inventory, and candidate metadata once;
  hash and parse the same bytes. Read each train/dev split once through a
  confined, single-link Windows handle, verify its pinned byte length and
  digest, then parse those exact bytes. Do not reopen a split by path after
  hash verification. Keep the held-out split unopened by the trainer.
- Pin the complete base-model tree before loading. Walk directories under
  retained no-write/no-delete handles; open every regular file without
  following reparse points and require one NTFS link. Hash each file from its
  retained read handle, compare the exact inventory, then keep all directory
  and file handles open while Transformers reads the path-based snapshot.
  Rehash the same handles after loading. Load the helper implementation from
  bytes matching the source hash fixed in this runner and the scorer receipt.
- Scratch accounting must enumerate entries without following links. Reject
  every Windows reparse point, hard-linked file, and unsupported filesystem
  entry in the per-job scratch tree. Pin the scratch root before starting the
  monitor or workload. Retain each discovered directory handle, denying
  delete sharing, until the monitor has stopped and final accounting finishes.
  Open file handles only for each sample, allow active writes, and close those
  file handles before the next sample. Re-scan the same pinned root and reject
  any root change. This prevents replacement of already pinned directories
  between samples. Newly created entries can still grow or change between
  samples, so the sampled byte cap remains an application monitor, not an OS
  quota or a bound on concurrent writers.
- Before a full fit, read the one-step preflight manifest and resource log
  through confined, single-link Windows handles. Bind the resource-log path to
  the fixed preflight job directory; hash and parse the same bounded bytes.
  Record both preflight hashes in the completed fit manifest. During monitor
  verification and finalization, likewise read each resource log once through
  a confined read-only handle and use the same bytes for floor/scratch checks
  and its manifest hash.
- If `WRENCH_LORA_ADDONS` is set, resolve it before adding it to `sys.path`;
  require the resolved directory to remain under `C:\\wrench-slm-data`.
- Check every optimizer step for finite gradient norm and finite trainable
  parameters after update. Save only to bounded staging, then promote after
  the staged adapter passes its byte cap and final resource check.

## Admission stages

1. Inspect exact processes and output paths. Run storage `status`, then reserve
   a unique job ID for the measured peak with all roots included. Confirm C:
   has sufficient free space. Keep every model/cache/temp path under
   `C:\wrench-slm-data`; the runner pins per-job cache and temp locations.
   Before the full-fit job creates artifacts, require at least 25% RAM free;
   if it is below this start buffer, stop that invocation before any output
   and retry only after live admission passes. The hard floor remains 10%.
2. Run a single bounded GPU preflight using the first eight training examples.
   It performs one optimizer step but writes no adapter. It must complete with
   finite loss, finite gradient/update, and preserve both resource floors for
   the entire process. Hash and retain its manifest and resource log. Before
   this step, obtain an independent exact-hash static review with PASS
   disposition. If the source changes after review, obtain another review. The
   already-preserved preflight attempt 01 failed before framework/model/data
   loading, and preflight attempt 02 passed. This revision authorizes only
   distinct preflight attempt 03 using the pinned local interpreter above. If
   attempt 03 fails, preserve it and do not launch fit attempt 02 or reuse any
   preflight ID/path.
3. After successful preflight, release that stopped job's reservation only
   after accounting for files. Run storage `status`, reserve a fresh unique
   fit job ID for the aggregate peak, and re-check current RAM, VRAM and C:
   free space immediately before training. Use only fit attempt 02's new ID,
   output paths, and the successful attempt-03 receipt; never reuse the failed
   fit-attempt-01 reservation, ID, log, snapshot, or adapter path.
4. Run exactly 96 steps. Check storage and resources before each epoch boundary
   and checkpoint boundary; there are no intermediate checkpoints. Keep the
   10% reserves throughout. On failure, preserve the receipt, write no adapter
   considered complete, and release only after the process stops and outputs
   are accounted for.
5. Verify the final manifest, exact 96-step count, adapter file set/hashes,
   fit-source hash, resource-log hash, finalized resource-log timestamp, and
   bounded runtime scratch totals. A finalization error must leave a failed
   receipt and nonzero process result, including a breach discovered after a
   success receipt was first written. Release the fit reservation only
   after accounting. Evaluator-source review and a separate dev-only runtime
   preflight are still required before the one-shot heldout scorer can open any
   heldout row.

## Interpretation

This is a compatibility and synthetic-policy screen. Passing does not prove
useful coding ability, a 95/5/95 result, real engineering quality, frontier
cost savings, or all-day operation. Do not use vendor benchmark scores or a
small synthetic heldout sample as production evidence. Keep all failed runs in
the record and never tune on the sealed final split.

## Component-aware LoRA design gate (2026-09-27 follow-up)

The preflight-03 receipt validates one optimizer step for the historical
all-module target profile. It is not evidence that this is the best Wrench
controller adapter. A Qwen3.5-0.8B component-placement preprint reports
attention-only LoRA with 24 modules / 1.08M trainable parameters versus
all-layer LoRA with 186 modules / 10.82M; outcomes were task-dependent, and
the study is single-seed and not Wrench-specific. It also reports sub-1B
HumanEval pass@1 <=0.6% after the tested placements. Source: [Where Should
LoRA Go?](https://arxiv.org/abs/2604.22127).

**Do not launch fit-02 under the existing all-module profile yet.** Before a
full fit, make and record the candidate-profile decision for this bounded
policy/evidence controller. The recommended comparison is all-module versus
softmax-attention-only, with the same frozen base, synthetic train/dev rows,
sequence cap and update schedule. If the target modules or runner changes,
create a new protocol revision, trainer hash, exact-hash review, unique
preflight/job IDs, fresh storage reservations, and a candidate-specific
preflight. Preflight-03 and fit-02 identifiers/receipts cannot be transferred
to a different target profile. Preserve the sealed heldout set.

This design gate is separate from the existing hardware gate: any fit still
requires >=25% free system RAM at process start and >=10% free RAM/VRAM during
the job. The smaller adapter parameter count may reduce optimizer state, but
does not prove the FP32 model load or activation footprint will shrink enough
to change the RAM admission decision.

## Attention-only candidate preflight (2026-09-27)

The trainer now exposes `--adapter-profile all-projections` and
`--adapter-profile softmax-attention-only`. The latter selects only
`q_proj`, `k_proj`, `v_proj`, and `o_proj` whose parent module is `self_attn`
under `model.language_model.layers.*`; it must match exactly 24 modules on the
pinned Qwen3.5-0.8B model. The all-projection profile retains the 186-module
allowlist. Both lists are covered by a CPU-only selection test, while the
candidate preflight will re-check the actual instantiated model with PEFT.

The authorized next GPU workload is only a one-step compatibility preflight
using `--preflight-only --adapter-profile softmax-attention-only`. It has new
job ID `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-04-ATTN`, log
directory
`C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-preflight-04-attention-only`,
and the normal per-job scratch directory under
`C:\\wrench-slm-data\\cache\\gateway-lora-screen-02\\<job-id>`. Reserve at
least 250,000,000 bytes for the job after a fresh storage status check. The
preflight writes only a bounded receipt and resource logs; it creates no
adapter and performs no heldout read. It proves target mapping, one optimizer
step, and resource compatibility only.

Before launch, independently review the exact trainer, test, protocol, and
iteration-record hashes. Then recheck live RAM and VRAM, destination free
space, and reservation. The job must retain at least 10% RAM and VRAM free.
This trainer revision rejects **every** full-fit invocation before runtime
bootstrap or artifact creation. Any later fit requires a new reviewed source
revision, protocol, separate fit ID/path, candidate comparison plan, fresh
preflight, and the existing >=25% free-RAM start gate.

Before writing run artifacts, the runner atomically creates a permanent claim
directory at
`C:\\wrench-slm-data\\cache\\gateway-lora-screen-02-claims\\<job-id>` and
writes its bounded `claim.json`. A duplicate invocation with the same ID exits
before writing a run receipt. Claim directories are retained; failed jobs
require fresh IDs and paths. Exception and finalization handlers write only
when the process successfully created that job's log directory. The claim and
receipt bytes are covered by the preflight reservation.

The historical all-projection preflight-03 receipt cannot approve the updated
trainer hash or the attention-only placement.

## Recorded attention-only preflight 04 result (2026-09-27)

Preflight `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-04-ATTN`
completed one finite optimizer update over eight synthetic train examples.
It attached LoRA to exactly 24 instantiated `self_attn` q/k/v/o modules and
recorded 540,672 trainable parameters. The runner saved no adapter, opened no
heldout row, and left runtime scratch at zero.

The preflight manifest SHA-256 is
`FFF6B5F6EF6F1BDF3904CEC21F303E56650D8D515B465CE83F8A6B197B97CA4A`; the
resource log SHA-256 is
`8438AD10B0398DE09BDC75E6AB9E10714C1E2AA4E477B779BBC1951A63179195`. All 58
resource rows matched the pinned RTX 5060 Ti identity; minimum free RAM was
12.5941%, minimum free VRAM 53.9697%, and scratch use was zero. The finalized
receipt confirms the runner hash and preflight-time protocol hash
`220261187631A9786DAABE4F0291C0E0C33EBD9A335ED0962EB835330B6BEE5D`.
The protocol file hash changes when this result is appended; the manifest
preserves the exact preflight-time identity.

The 250,000,000-byte reservation is releasable only after the final log,
claim, and resource files are accounted and a fresh storage check confirms the
aggregate remains below 50 GB. This one-step receipt does not admit a full fit
or establish any Wrench policy quality, code ability, or product target.

## Attention-only fit path 03 (2026-09-27)

The owner-selected candidate for the first bounded Wrench LoRA is
`softmax-attention-only`, because this policy predicts finite evidence/context
and route choices rather than generating code. The active trainer CLI accepts
only this profile. It must attach to exactly 24 `self_attn` q/k/v/o modules and
instantiate exactly 540,672 trainable parameters on the pinned Qwen3.5-0.8B
revision. The 186-target all-projection profile remains only as a historical
selector comparison and is not admitted by the active runner. This is an
experimental placement choice, not evidence of better policy quality.

The new identities are unique and cannot reuse preflight 04 or fit 02:

| Job | ID | Output |
|---|---|---|
| Candidate preflight | `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-05-ATTN` | `C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-preflight-05-attention-only` |
| Candidate fit | `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN` | `C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\lora-screen-02\\fit-03-attention-only` and `C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-fit-03-attention-only` |

After an exact-hash independent review of the runner, focused tests, this
protocol, and the iteration record, preflight 05 may run one optimizer step
over eight synthetic train rows with a fresh reservation of at least
250,000,000 bytes. At admission and each checkpoint, destination free space
must be at least the active reservation plus 5 GiB of operating headroom. Its
receipt must bind this runner/protocol/data/model/runtime
identity, the attention-only profile, 24 target modules, and 540,672 trainable
parameters. It must save no adapter, read no heldout row, and preserve at least
10% RAM and VRAM. Record minimum sampled free-RAM and free-VRAM fractions from
the hash-bound resource log in the manifest. Account for and release the stopped preflight reservation
before admitting fit 03.

Fit 03 requires a fresh reservation of at least 1,500,000,000 bytes, destination
free space of at least that reservation plus 5 GiB of operating headroom, at
least 25% free RAM before process start, and at least 10% free RAM and VRAM
throughout. It may run only after
preflight 05 completes successfully and its reservation is released. Fit 03
uses only the synthetic 256-row train and 64-row dev splits, three epochs,
gradient accumulation 8, and exactly 96 optimizer steps. A hard check before
every update prevents any step beyond 96; successful finalization requires
exactly 96. No early stopping, heldout access, provider request, or adapter
activation is allowed.

The fit writes to a unique staging directory and verifies every regular,
single-link file under the approved root before and after atomic finalization.
It uses a Windows atomic no-replace rename, so a destination created after the
precheck cannot be silently replaced. The final file inventory and hashes
must equal the staged inventory; the staging path must disappear. Any mismatch, resource breach, or finalization
error yields a failed/non-promotable receipt. The adapter remains an inactive
candidate and cannot replace the foundation, installed Core, or an active
adapter. Before heldout scoring, the scorer must be revised to consume fit
03's new ID and paths, receive its own exact-hash review, and retain the
one-shot heldout lock and independent dev-only inference preflight.

The current RAM snapshot is below the 25% fit-start gate. No preflight 05 or
fit 03 has run. If review passes, repeat live admission immediately before
preflight; repeat storage, RAM, VRAM, and free-space checks before fit. A
preflight pass still establishes compatibility only. It does not establish
Wrench decision quality, code ability, full-day operation, or any 95/5/95
target.
