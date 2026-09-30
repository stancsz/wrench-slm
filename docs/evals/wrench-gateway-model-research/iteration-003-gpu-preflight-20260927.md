# Iteration 003: GPU LoRA preflight

Status: **preflight 03 passed one optimizer step after assignment 27 static PASS; fit 01 aborted below the 10% RAM floor; fit 02 is pending a fresh reading of at least 25% free RAM**.

The original job IDs in the initial frozen-identities section below are
historical and superseded. Current preflight 03 and fit 02 identities and
receipts are recorded in the latest dated section at the end of this file.

Screen 01's CPU/FP32 full fit stopped when free RAM fell to 9.72%. No adapter
or optimizer step was produced. This iteration tests only whether the same
pinned 0.8B LoRA setup can execute one optimizer step on the currently observed
RTX 5060 Ti in FP32 while keeping at least 10% system RAM and VRAM free. It
does not change the model, data, targets, labels, sequence cap, hyperparameters,
frozen installed adapter, or held-out split.
Before any Wrench-owned input is read, the resolved dataset root, model root,
inventory, and reservation must remain below `C:\\wrench-slm-data`; the trainer
fails closed on junction or symlink redirection.

## Frozen identities and limits

- Runner: [GPU screen-02 fit](../../../tools/train_gateway_lora_screen_02_gpu.py)
- Training protocol: [GPU screen-02 protocol](lora-screen-02-gpu-protocol-20260927.md)
- Held-out protocol: [screen-02 scoring protocol](heldout-eval-protocol-20260927.md)
- Base: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, verified local snapshot.
- Data: existing synthetic train/dev files, 256/64 rows; heldout remains sealed.
- Device: `cuda:0`, FP32, current observed GPU `NVIDIA GeForce RTX 5060 Ti`.
- Device identity: index `0`, UUID
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.
- Pinned candidate metadata SHA-256:
  `6CEFDBBD0203D8E78EB1DEE655E82C65EFCFA425B57A80CB335242645F47F0A9`.
- Pinned dataset manifest SHA-256:
  `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED`.
- Preflight job ID:
  `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-01`.
- Preflight reservation: at least 250,000,000 bytes for bounded receipt and
  resource output plus the 128 MiB per-job runtime scratch cap. It writes no
  adapter. Scratch and OS temporary paths live under the approved data root;
  resource samples and finalization record measured bytes. The cap is
  monitored by the runner, not enforced by an OS quota.
- Full-fit job ID (only after passing preflight):
  `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-01`.
- Full-fit reservation target: 750,000,000 bytes for the capped adapter,
  receipts, logs, and the 512 MiB per-job runtime scratch cap; remeasure before
  reserving.

The preflight is one optimizer step over the first eight training examples.
It passes only if loss, gradient norm, and updated trainable parameters are
finite, all model parameters are on the pinned `cuda:0`, the manifest and
resource log finalize and hash correctly, and every recorded sample remains
above both 10% floors. A failure or resource breach blocks the full fit under
this protocol. Preserve the receipt and release only the stopped preflight
reservation after accounting. The exact source set must receive a fresh
independent exact-hash static review with PASS disposition before this
preflight. Review assignment 09 failed and identified unsafe manifest path
resolution, scorer reservation checks, GPU identity, and receipt finalization
gaps. Those sources and protocols have since been hardened; assignment 09 does
not cover their new hashes. Do not access heldout or run the scorer until a new
review passes, the full fit completes, and the separate development-only model
preflight succeeds.

## Current admission snapshot

At 2026-09-27 09:43 UTC, after screen 01 exited, host RAM free was 21.93% and
the GPU reported 15,193 MiB free of 16,311 MiB. C: had 166,116,487,168 bytes
free in the earlier 09:24 snapshot; re-check disk and storage immediately
before reserving the preflight. The failed screen-01 fit reservation has been
released. This is a fresh job and receives a fresh unique reservation.

No preflight has run, no training is active, no adapter exists, no held-out
record has been opened, and no provider generation request has been sent.

## Static review update (2026-09-27 10:55 UTC)

Assignment 13 (`WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-13-20260927-01`,
nonce `a1d7fb86-2a14-4c12-8eea-4bd5ee68fa25`) failed on one P1 held-out gate
defect and three P2 hardening findings. The held-out scorer compared the dev
preflight resource log against the held-out scratch cap; the training runner
did not confine `WRENCH_LORA_ADDONS`; adapter child paths were not individually
resolved; and a finalization-discovered resource breach could leave exit code
zero. These findings are being fixed in the runner and protocol. Assignment 13
does not cover the modified hashes. No preflight or held-out access occurred.

## Static review update (2026-09-27 11:05 UTC)

Assignment 14 verified the four assignment-13 fixes but failed on two
conditional P2 path findings: the scorer opened the global held-out lock
without resolving/rejecting links, and it hashed/read the fixed training
resource log without file-level containment. The scorer now resolves the lock
parent and final lock target before any lock write, and resolves/contains the
training resource log before hashing or reading. These bytes require another
exact-hash read-only review; no preflight or held-out access occurred.

## Static review update (2026-09-27 11:18 UTC)

Assignment 15 (`WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-15-20260927-01`,
nonce `e15d63bd-6676-42c9-93fb-ccaa164b05b2`) failed on a conditional P2
time-of-check/time-of-use race: the scorer validated the lock path, opened it
by path, then checked the name again, leaving a window where a reparse target
could be swapped and restored around the write. The budget check also used
path-based lock metadata before confinement. The scorer now opens the lock
with Windows no-reparse-point handles, validates the live parent and file
handles before writing, uses `fstat` for budget accounting, and holds the
one-shot marker handle without delete sharing while the held-out job runs.
Marker reads also use validated handles. Assignment 15 does not cover these
new hashes. A fresh exact-hash read-only review is required; no preflight,
fit, held-out access, or provider generation has occurred.

## Static review update (2026-09-27 11:32 UTC)

Assignment 16 (`WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-16-20260927-01`,
nonce `e966e04e-9932-415b-ab67-2455c06ad632`) verified its four assigned
hashes and failed on two conditional P2 findings: the handle verifier did
not reject an NTFS hard link, and the fixed training resource log was hashed
and reopened separately for parsing. The scorer now requires a single link
for confined child files, opens resource logs read-only with write sharing
denied, reads them into one bounded byte buffer, and hashes and parses those
same bytes. The preflight log is bound to its job ID and uses the same read
path; the user-supplied preflight receipt is also bound to its job ID and read
once through a confined single-link handle. Failure receipts use the bounded
reader too. These changes need a new
exact-hash review. No GPU preflight, fit, held-out access, or provider
generation has occurred.

## Static review update (2026-09-27 11:41 UTC)

Assignment 17 (`WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-17-20260927-01`,
nonce `c7d7ccd7-a5ab-46fc-abac-bf3c2a0be3a2`) matched all four hashes and
failed on three conditional P2 findings: the scorer read and hashed the
training manifest separately; the trainer accepted and reread a declared
preflight log by path instead of binding it to the fixed preflight directory;
and trainer finalization parsed one resource-log read but hashed another. The
scorer now reads the training manifest once from a confined single-link
handle. The trainer reads the preflight receipt and fixed resource log through
confined single-link handles, hashes and parses each same byte buffer, binds
the path to the preflight job directory, and records both fit-preflight
hashes. Monitor and finalization resource checks also use one bounded buffer
for parsing and hashing. These changed hashes require a fresh review. No GPU
preflight, fit, held-out access, or provider generation has occurred.

## Static review update (2026-09-27 11:48 UTC)

Assignment 18 (`WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-18-20260927-01`,
nonce `7e5237a3-7f09-4a8c-9229-20260927e018`) matched all four hashes and
failed on one P1 and two P2 findings. Training/dev split hashes were checked
before later path-based opens, leaving a conditional race that could admit
changed training rows. Held-out prompts and labels were separately re-read
after hash checks. The trainer and scorer now read train/dev bytes once through
confined single-link handles, verify and parse the same bytes, and the scorer
reuses one verified held-out buffer for prompts and the post-prediction label
pass. Both scratch walkers now reject Windows reparse points, hard-linked
files, and unsupported filesystem entries while scanning without following
links. The trainer also reads its candidate, inventory, and data manifest once
before hashing/parsing. These changes require assignment 19 exact-hash review.
No GPU preflight, fit, held-out access, or provider generation has occurred.

## Static review update (2026-09-27)

Assignment 19 matched the assigned source and protocol hashes, then failed on
two conditional P2 findings. The trainer and scorer hashed model files before
Transformers reopened them by path; the scorer had the same gap for adapter
files, and its adapter check did not reject NTFS hardlinks. Both scratch
walkers also left a directory-replacement window around path-based
`os.scandir`.

The trainer and scorer now load a small Windows tree helper only from bytes
whose SHA-256 is pinned in both sources. The helper opens every ancestor
directory below the approved root and each file with reparse inspection,
validates final paths and live file IDs, rejects hardlinks, and holds model and
adapter handles with read-only sharing across Transformers/PEFT loads. It
rehashes those same handles after loading. Scratch accounting retains directory
and file handles that deny delete sharing during each scan while allowing
active writes; it checks all entry types and sizes. This is still a monitored
cap, not an OS quota. These changes need assignment 20 exact-hash review.

No Screen 02 preflight, fit, model inference, held-out access, or provider
generation has run. The current source remains unapproved until independent
review 20 passes. Keep the 10% RAM/VRAM and 50 GB storage gates in force; this
source change does not admit a run.

## Static review update (2026-09-27)

Assignment 20 matched the seven assigned hashes but stopped before final
review because the research report changed after assignment began. Its
disposition is **UNVERIFIED**, not PASS or FAIL. The reviewer identified a
conditional P2 gap: each scratch sample closed all directory handles, so the
scratch root could be replaced between samples. The trainer and scorer now
retain directory handles that deny delete sharing for the full job, rescan only
the same root, and open file handles only during each sample. The root is
pinned before the monitor/workload proceeds; handles are released only after
monitor shutdown and final accounting. This is an application-level sampled
cap, not an OS quota, and concurrent growth remains possible. The exact new
source and protocol hashes need an independent review before any preflight,
fit, inference, or held-out access. No such job has run.

## Static review update: assignment 21 (2026-09-27)

Assignment 21 matched all seven hashes and failed on two P2 issues in the
scorer. The monitor thread and main thread could scan the same scratch tree at
once, and the post-monitor final scratch measurement was omitted from the
receipt peak. The scorer now serializes scans and releases, uses the monitor's
latest sample for concurrent output-budget checks, then records an explicit
post-monitor `runtime_scratch_bytes_at_finalize` included in the peak. The
changed source and protocol hashes need a new independent review. No preflight,
fit, inference, or held-out access has run.

## Static review update: assignment 22 (2026-09-27)

Assignment 22 matched all seven hashes and confirmed the assignment-21 fixes,
then found one P2 race in the scorer's aggregate output cap: prediction lines
and monitor resource-log lines could pass independent checks and jointly
exceed the cap. The scorer now shares one output-budget lock across each
check-and-write sequence, including JSON replacement and the global marker and
lock bytes. The changed source and protocol hashes need another exact-hash
review. No GPU or held-out job has run.

## Static review update: assignment 23 (2026-09-27)

Assignment 23 matched all seven assigned hashes and confirmed the assignment-
21/22 fixes, then failed on one P2 aggregate-output-cap race. The held-out lock
owner JSON was written after releasing the shared output-budget lock, while the
resource monitor could append a row. The scorer now serializes a fresh budget
check and lock-owner metadata replacement under the same shared lock, after
acquiring the OS-held lock. The existing lock-file size is counted
conservatively. This fix needs another exact-hash independent static review.
No preflight, fit, inference, or held-out access has run.

Assignment identity: `WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-23-20260927-01`
(nonce `6bc91208-a7f0-4414-878b-277a569df031`); expected repository HEAD was
`af01304824f079a64b6c3902397a2034b843511a`. Disposition: **FAIL, P2**. The
review was static. No model/dataset/held-out access, inference, training,
provider calls, credentials, network access, or spending occurred.

## Static review update: assignment 24 (2026-09-27)

Assignment 24 matched all seven assigned hashes before and after review and
found no P1/P2 issues. It confirmed the assignment-23 owner-metadata fix,
assignment-21/22 scratch and output serialization, and the final resource
receipt checks. Disposition: **PASS**, static evidence only. The GPU preflight
is now clear of the source-review gate, but requires its own storage
reservation, current output/process checks, and live 10% RAM/VRAM admission.
No preflight, fit, inference, or held-out access has run as of this update.

Assignment: `WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-24-20260927-01`;
nonce `54294fb6-91b3-4aa6-98df-61d8a9de3216`; expected and observed HEAD before
and after: `af01304824f079a64b6c3902397a2034b843511a`. All pre/post hashes
matched:

| File | SHA-256 |
| --- | --- |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `tools/train_gateway_lora_screen_02_gpu.py` | `5FA9324171C2D7B77057F7B8D7B22CBFB251AEB86D5A078BD09C2F24D933F37B` |
| `tools/score_gateway_lora_screen_02.py` | `0A81199971A4639BC67318D034C37DD7B6926B70359F83525CF2D616B00490FF` |
| `lora-screen-02-gpu-protocol-20260927.md` | `2520249073CD34F8528A9505C7008B7F0C42A8CAFF7A6F09FDFE2E044091D5C7` |
| `heldout-eval-protocol-20260927.md` | `5BD2BE26B38DB00F477DECF69BA4FBEE754D61D457F96B8A065126E31B9750D9` |
| `iteration-003-gpu-preflight-20260927.md` | `053865C8634340E9C0F20F3A04340AD9C2F8727E592182EBAA810C35E53EFAC7` |
| `research-20260927.md` | `45F55A9B5DA72877BFD964BC8C8117CDDDC8EBFFBD17E095C6B5266D05CA4B7D` |

Reviewer used only the assigned read-only commands and AST parse. No runtime,
dataset, held-out, model, provider, credential, network, or spend access
occurred; no files changed. This review does not replace the runtime preflight.

The hashes above are the exact assignment-24 pre/post snapshot. This iteration
log and the report were extended after the reviewer returned. The runner and
protocol hashes from that snapshot were unchanged through the separately
recorded attempt-01 bootstrap failure below; the revised attempt-02 runner and
protocol are a new revision awaiting a new review.

## GPU preflight attempt 01 (2026-09-27)

The one-step GPU preflight was launched with the unconfigured AppData
`python.exe` (Python 3.13.15), which lacked PyTorch. It exited at
`import torch` with `ModuleNotFoundError: No module named 'torch'`, before
reading candidate metadata, the model inventory, dataset manifest, train/dev
rows, or held-out data and before any optimizer step. Its preserved receipt is
`FAILED`, reports `heldout_opened_by_runner=false`, has null model-inventory and
dataset-manifest hashes, and records zero scratch bytes. The resource log's
single sample has the expected GPU UUID, 18% free system RAM, and 93% free
VRAM. No adapter was written.

Attempt identity: `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-01`.
The manifest at
`C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-preflight\\run-manifest.json`
is 2,211 bytes with SHA-256
`74A799AC306514BE788C656D43082671F89BE9AA1B1AEA8D79580B4BD1251837`; the
840-byte resource log has SHA-256
`6ECC5429E2629D554B726862EFEA7CC63599DD9E498BEF56520536254F7C3950`. The
empty scratch tree and both outputs were accounted for; its 250,000,000-byte
reservation was released. No model, dataset, held-out, provider, network,
credential, inference, successful preflight, or training use occurred.

An existing approved local runtime was found at
`C:\\wrench-slm-data\\envs\\wrench-local-synthetic-cp313\\Scripts\\python.exe`
(Python 3.13.15, torch 2.14.0+cu132, transformers 5.17.0), with PEFT 0.21.0
and Accelerate 1.15.0 in the approved add-on directory
`C:\\wrench-slm-data\\envs\\wrench-gateway-lora-screen-01-addons`. No
dependency installation or download was performed. The runner and protocol
now select distinct attempt `...PREFLIGHT-20260927-02` and log directory
`lora-screen-02-preflight-02`; this revision must pass a fresh exact-hash
review and fresh storage/resource admission before it runs. An attempt-02
failure ends this protocol; no job ID or log path is reused.

## Static review update: assignment 25 and runtime identity remediation

Assignment 25 (`WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-25-20260927-01`,
nonce `f20831c4-2298-4a2f-b271-3d78f03c594e`) matched all eight assigned
hashes and failed with one P2. The runner logged Python and package versions
without enforcing the approved interpreter, add-on directory, or versions,
and fit did not compare those fields with the preflight receipt. The remediation
now rejects any interpreter other than the exact approved Python 3.13.15 and
requires the exact approved add-on directory before creating artifacts. After
imports, it enforces Torch 2.14.0+cu132, Transformers 5.17.0, PEFT 0.21.0, and
Accelerate 1.15.0; checks package origins against the approved environment and
add-on tree; and records paths and versions in the manifest. Fit now requires
exact runtime identity equality with attempt 02's receipt. The revised runner,
protocol, and evidence need assignment 26 exact-hash review before admission.
No preflight, fit, held-out read, inference, or provider call occurred as part
of assignment 25 or this remediation.

## GPU preflight attempt 02 (2026-09-27)

Assignment 26 (`WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-26-20260927-01`,
nonce `19dc55a8-60d5-4cf1-8395-499619b82af0`) passed exact-hash static review
of eight assigned files. The one-step attempt 02 then used the exact approved
Python 3.13.15 executable, Torch 2.14.0+cu132, Transformers 5.17.0, PEFT
0.21.0, and Accelerate 1.15.0; the receipt pins module origins to the venv
and add-on directories. It completed one optimizer step on eight synthetic
training examples with finite update checks. It read only the existing
synthetic train/dev split, left held-out unopened, and wrote no adapter.

Receipt: `C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-preflight-02\\run-manifest.json`, SHA-256 `BD057199FFB37782830C99676EB7AB4BF1C9E89AEB495673A1ED05F8BCD136A9`; resource log `...\\resources.jsonl`, SHA-256 `F1BED6939E21DDCC88A26D4A938D1390E12DFEB038EB1284398A81629599349F`. Across 103 resource samples, minimum free RAM was 11.31%, minimum free GPU memory was 53.79%, GPU UUID matched the pin, and peak/final scratch was 0 bytes. Its 250,000,000-byte reservation was released after output accounting. This preflight establishes only runtime/optimizer-step compatibility.

## Full fit attempt 01 (2026-09-27)

The distinct 96-step fit job
`WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-01` started under the exact
preflight-matched runner, protocol, data, model, runtime identity, and GPU. It
aborted at 2026-09-27 13:32:51 UTC with
`status=ABORTED_RESOURCE_OR_INTERRUPT` and
`abort_reason=RAM_FREE_BELOW_10_PERCENT`. The 29-row resource log recorded a
minimum RAM-free fraction of 0.098283 (9.83%) and minimum GPU-free fraction of
0.725277 (72.53%). The manifest has no optimizer step count. Held-out stayed
unopened. Adapter and staging paths do not exist; the bounded 63,758-byte
runner snapshot is preserved at
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\lora-screen-02\\train_gateway_lora_screen_02_gpu.py`
with SHA-256 `461DCD658558E1925CD34C2A26CE6F16AC421D4534DA2D318DD7E73B4D75EE1A`.
Manifest SHA-256 is
`F3916F5E1A246CF035BF17A38D55081E75853C0BA5E8EE52842AC95722EB65DD`; resource
log SHA-256 is
`83EDD0DA5E91FF090B234D2FD2D8231C917E37C942345A9D2025B4AC50383D4C`. The
750,000,000-byte reservation was released only after the process exited and
all outputs were accounted for. This is a resource failure, not a model
quality result. Any retry needs fresh attempt IDs/paths and a new source and
protocol hash review, followed by a new preflight bound to that revision.

## Retry revision after the RAM-floor abort

The next revision keeps the same pinned 0.8B FP32 model, synthetic train/dev
rows, labels, LoRA targets, sequence cap, and optimizer schedule so the retry
isolates the host-memory admission issue. The runner now refuses to create fit
artifacts unless RAM free at process start is at least 25%, while its monitored
runtime hard floor stays at 10% RAM and VRAM. It records the observed start
fraction and required threshold. A new attempt uses preflight
`WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-03` at
`lora-screen-02-preflight-03`, followed only after success by fit
`WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-02` at `lora-screen-02-fit-02`
and fresh `fit-02` artifact paths. Assignment 27 exact-hash review is required
before preflight 03. If live RAM is below 25% before full-fit admission, defer
the run and continue independent work; do not lower the start buffer or reuse
fit attempt 01's ID, paths, reservation, or snapshot.

## Current preflight 03 result and fit 02 gate (2026-09-27)

Assignment 27 (WRENCH-GW-SCREEN02-STATIC-REVIEW-ASSIGNMENT-27-20260927-01,
nonce 7f98d40b-2362-466b-a331-52bcdb9d7fc7) passed exact-hash review at
HEAD af01304824f079a64b6c3902397a2034b843511a, with all eight assigned
source/protocol/report hashes matching before and after. No P1/P2 blocker was
reported. The review confirmed that fit 02's 25% RAM admission check precedes
artifact creation, preflight 03/fit 02 IDs and paths are distinct, the scorer
is bound to fit 02, and heldout access follows the separate evaluator gates.
The exact reviewed revisions were:

| File | SHA-256 |
| --- | --- |
| tools/wrench_windows_pinned_tree.py | E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499 |
| tools/train_gateway_lora_screen_02_gpu.py | D1EA068B5EFEACD7A318EBFF4217FACFD1FA01AF3B7FB8CE08689AD18728B5CE |
| tools/score_gateway_lora_screen_02.py | D26BB712C452A2E62FE9015CA287ADB72974815CEB48AA91B7D9862DB2D7DF72 |
| lora-screen-02-gpu-protocol-20260927.md | 7F894E578C2264190DFF551499C0C83194F49431DC383E9825DC458630589557 |
| heldout-eval-protocol-20260927.md | 2D6CA677A1A000C1820302B6501E390813CE6CC4574BF28EE694BA060F5BD53B |
| iteration-003-gpu-preflight-20260927.md | C506997356D61B27574758FC201BD1F9DDC5D07CF67A840DB308883ED7DE45DA |
| research-20260927.md | 3E0A0C8867C096C9662B8A4BE9588E739A0D1C7FAAAF9F0D0ED125D211BF4F02 |
| docs/goal/wrench-gateway-model-research/GOAL.md | B46C60E781740D7FDAFA82E69F983E83519EAC686C97ABADD11C65A6CDC4154F |

Preflight WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-03 completed
one optimizer step on eight synthetic training examples. It used the pinned
0.8B model/data, exact approved Python 3.13.15 runtime and add-on paths, Torch
2.14.0+cu132, Transformers 5.17.0, PEFT 0.21.0, and Accelerate 1.15.0. It
recorded 107 resource rows, minimum free RAM 12.3796%, minimum free VRAM
53.6203%, zero runtime scratch, and heldout_opened_by_runner=false; no
adapter was created. Manifest SHA-256:
7EB4766FE0DE2B4A2C81E1A33E6508D361898B5934DDD110F941C2CE294E60CB.
Resource-log SHA-256:
90AED6C7D12491D39381E2C1C5EF6A09A55829BC5B7C337A7996523FBEE035B7.
Its 250,000,000-byte reservation was released after output accounting.

Fit WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-02 has not started.
Latest host RAM was below the 25% start buffer, so wait for a fresh resource
sample at or above that threshold before reserving and launching the fit.
Keep the 10% monitored RAM/VRAM floors unchanged. No heldout data has been
opened and no quality result exists.

## Fit-01 memory source and receipt analysis (2026-09-27)

Assignment `WRENCH-GW-FIT02-MEMORY-REVIEW-20260927-02`, nonce
`7a7d1c4e-9274-4894-88fe-b6b71392`, analyzed the actual fit-01 receipts and
the current trainer at HEAD `af01304824f079a64b6c3902397a2034b843511a`.
Disposition: source-and-receipt analysis only; it does not admit a runtime job.
All seven assigned repository and receipt hashes matched before and after the
read. The exact hashes are in the assignment handoff.

Fit-01 fell from 16.70% free RAM (5.73 GB) to 9.83% (3.37 GB) in about 34.7
seconds, a drop of about 2.36 GB. The last sample fell from 14.16% to 9.83%
while free VRAM moved from 15,083 MiB to 11,830 MiB. The whole-machine RAM
telemetry cannot identify the responsible process. The fit-01 manifest pins an
older runner snapshot (`461DCD...`), so it does not prove the current trainer
caused the same drop. Preflight-03 ran the current trainer hash and reached a
12.38% minimum RAM with 53.62% VRAM free. The current trainer loads FP32
weights directly to the pinned GPU with `low_cpu_mem_usage=True`, uses
gradient checkpointing, batch size 1 and gradient accumulation 8. The 5.41M
trainable adapter parameters are small next to the 858.4M base model.

**Decision:** keep fit-02 unchanged and wait for live RAM at or above 25% free.
At the recorded 18.47% sample this is about 2.24 GB short. If another reviewed
source revision is justified, deleting raw row references after tokenization
may recover a small amount, but the 320 train/dev rows are not enough to infer
a multi-gigabyte benefit. BF16/QLoRA or a shorter sequence cap changes the
protocol and requires a distinct job, review and preflight. Do not lower the
start gate or stop services to force admission.

No model, dataset, heldout content, training workload, inference, provider,
credentials, or process/service changes were used in this analysis.

## Follow-up: component-aware LoRA placement gate (2026-09-27)

A new preprint directly studies adapter placement on Qwen3.5-0.8B. It reports
24 softmax-attention modules / 1.08M trainable parameters for attention-only,
versus the 186 modules / 10.82M parameters used by its all-layer profile.
The paper finds domain-dependent quality and forgetting tradeoffs and is a
single-seed non-Wrench study. The current Wrench task is bounded policy and
evidence selection, so attention-only is a meaningful comparison before
spending a full fit on the current all-module profile. Source: [Where Should
LoRA Go?](https://arxiv.org/abs/2604.22127).

**Updated gate:** fit-02 remains unstarted and must not use its existing
all-module profile until a reviewed protocol records whether it will compare
attention-only versus all-module placement or provides a documented reason to
retain only the latter. The preflight-03 one-step receipt remains valid for
its exact old trainer hash, but it is not a quality result and cannot approve a
changed target list. A changed trainer/profile needs a new unique runner hash,
exact-hash review, job IDs, fresh reservations, and candidate-specific
preflight. The 25% RAM start gate and 10% runtime floors remain unchanged.

Latest recorded RAM (17.74%) is below the 25% start gate, so resource admission
also remains closed. No code, dataset, heldout data, model weights, or adapter
were changed or used for this follow-up.

## Profile-selection implementation and attention-only preflight gate (2026-09-27)

Added an explicit trainer profile selector. `all-projections` preserves the
historical 186-module allowlist. `softmax-attention-only` restricts targets to
the four q/k/v/o projections whose parent is the model's `self_attn` block and
asserts exactly 24 actual modules after loading the pinned model. A focused
CPU-only test uses the previous exact target manifest's six full-attention
layers to check both profile counts and rejects a changed attention target
count. This test is selector verification, not a model run or quality result.

The attention-only compatibility preflight has the unique job ID
`WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-04-ATTN`, log directory
`lora-screen-02-preflight-04-attention-only`, and candidate-specific scratch
directory derived from that job ID. It is restricted to one optimizer step,
synthetic train rows, no heldout access, and no saved adapter. A full fit for
every profile is rejected by the runner before runtime bootstrap in this
revision. Assignment 27 and preflight 03 refer to old source hashes and do not
authorize this revision.

Before preflight 04: complete the focused test, run `git diff --check`, record
exact hashes for the trainer/test/protocol/iteration record, obtain an
independent static review on those exact hashes, then make a fresh storage
status/reservation and device sample. Require >=10% RAM and VRAM free through
the bounded job; retain >=25% RAM at any later full-fit start. Do not use
SubRoute or incur provider spend for this compatibility screen.

Before writing run outputs, the runner now atomically claims the unique job ID
under `C:\\wrench-slm-data\\cache\\gateway-lora-screen-02-claims`. Claims are
permanent; failures require a fresh job ID. Receipt and finalization handlers
write only when the process created that run's log directory.

### Assignment 28: exact-hash review failed before preflight 04

Assignment `WRENCH-GATEWAY-LORA-ATTN-PREFLIGHT-REVIEW-20260927-01`, nonce
`87133307-0fff-43b8-aa9b-ece5079bdefe`, matched all four assigned hashes and
HEAD `af01304824f079a64b6c3902397a2034b843511a` before and after review. It
returned **FAIL** with two P2 findings:

1. The all-projections full-fit path was still reachable. Its stale preflight
   would fail only after log/scratch creation, framework setup, and train/dev
   reads. Corrected by closing all full-fit invocations before runtime
   bootstrap in this revision.
2. Concurrent calls with the same job ID could race at run-log directory
   creation, after which the losing process's failure handler could overwrite
   the winner's receipt. Corrected with an atomic permanent per-job claim and
   an `owns_artifact_dir` guard for failure/finalization writes.

The reviewer confirmed the 24-module attention filter, 186-target baseline,
distinct preflight 04 paths, one-step/no-adapter behavior, and no heldout
access. The reviewer also confirmed that the fixture itself did not read the
historical target manifest. No runtime, model, heldout, provider, or spend
activity occurred. Corrected hashes require a fresh independent exact-hash
review; preflight 04 remains unstarted until it passes.

### Assignment 29: corrected exact-hash review passed

Assignment `WRENCH-GW-SCREEN02-ATTN-STATIC-REVIEW-ASSIGNMENT-29-20260927-01`,
nonce `e05cc8da-0503-4149-837b-9931784a8fc2`, returned **PASS** for the
bounded attention-only preflight, with no P1/P2 findings. HEAD and all six
assigned hashes matched before and after:

| File | SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_02_gpu.py` | `545379E87FF3AAE528611C8FB2FA25BFEC631DF4486E953523F25749BAFC26CF` |
| `tests/test_gateway_lora_profiles.py` | `28485692B02B378956782723A8B283A490E118C38AD3F4E4F9C980902FD7B24E` |
| `lora-screen-02-gpu-protocol-20260927.md` | `220261187631A9786DAABE4F0291C0E0C33EBD9A335ED0962EB835330B6BEE5D` |
| `iteration-003-gpu-preflight-20260927.md` | `880A34F79D2507944FADA59931B062F5C3FC72C714FFE0F6476CBCD1069AA737` |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `D5084C5EDE474BC942D8C1F2C045D2F59CCA7CB8E6397B3A4B42F80518A7C5E3` |
| `docs/reports/wrench-gateway-model-research/research-20260927.md` | `F0426547C1FB1C5285EB6B1F37FE5B1B3EB28571C3EB508A0E9B2EB3BDA801D1` |

The reviewer verified early rejection of every full-fit CLI path, atomic
permanent job-ID claims before run artifacts, owner-gated receipt/finalization
writes, profile target counts and path separation, and the one-step/no-adapter/
no-heldout scope. The synthetic selector fixture was not compared to a
hash-bound historical manifest, so only runtime preflight can verify the
instantiated module map. The only note was that deliberately recreating the
spent all-projections preflight-03 reservation could leave an orphan claim
before an existing-path guard; it cannot overwrite outputs or start work and
does not block authorized preflight 04.

This static PASS does not itself admit execution. Preflight 04 still needs a
fresh storage status and 250,000,000-byte reservation, live RAM/VRAM and C:
space checks, exact approved interpreter/add-on identity, and post-run
receipt/accounting. No inference, training, heldout, provider, or spend action
has occurred for this candidate.

### Attention-only preflight 04 execution receipt

After Assignment 29 passed, the preflight was admitted under a fresh
250,000,000-byte reservation. Job
`WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-04-ATTN` finished with
`PREFLIGHT_COMPLETED`, exactly one optimizer step over eight synthetic
examples. The pinned Qwen3.5-0.8B revision
`2fc06364715b967f1860aea9cf38778875588b17` attached LoRA to exactly 24
`self_attn` q/k/v/o modules, with 540,672 trainable parameters. This verifies
actual target mapping and single-step compatibility, not useful policy
behavior. No adapter was saved and `heldout_opened_by_runner=false`.

Manifest SHA-256:
`FFF6B5F6EF6F1BDF3904CEC21F303E56650D8D515B465CE83F8A6B197B97CA4A`.
Resource-log SHA-256:
`8438AD10B0398DE09BDC75E6AB9E10714C1E2AA4E477B779BBC1951A63179195`.
The 58 resource rows identify the pinned RTX 5060 Ti and show minimum free
RAM 12.5941%, minimum free VRAM 53.9697%, and zero runtime scratch, all within
the required 10% floors. The manifest runner hash matches Assignment 29's
reviewed source hash. Its protocol hash pins the preflight-time bytes
`220261187631A9786DAABE4F0291C0E0C33EBD9A335ED0962EB835330B6BEE5D`.
Files were confined to the approved log and claim paths; no adapter output
path was created. The run used the approved Python 3.13.15, Torch
2.14.0+cu132, Transformers 5.17.0, PEFT 0.21.0, and Accelerate 1.15.0
environment, offline.

This does not prove model quality, 95% local completion, <=5% frontier
escalation, 95% frontier-token savings, 95% lower all-in cost, or all-day
engineering. Full fit remains closed by the current runner revision. Account
for final receipt and claim bytes and run storage status before releasing the
preflight reservation.
