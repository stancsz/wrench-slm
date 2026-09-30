# Gateway screen 02 held-out scoring protocol

Date: 2026-09-27 (America/Edmonton)
Status: revised for screen-02 attention-only fit attempt 03; no held-out scoring has started. The access gate requires a completed 96-step fit, released training storage, and a completed development-only runtime preflight.
Goal: [gateway LoRA and token-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)
Training protocol: [GPU LoRA screen 02](lora-screen-02-gpu-protocol-20260927.md)
Preflight receipt: [iteration 002](iteration-002-lora-preflight-20260927.md)
Scoring implementation: [score_gateway_lora_screen_02.py](../../../tools/score_gateway_lora_screen_02.py)

## Access gate

Do not open or score the held-out JSONL until the screen-02 GPU LoRA training run has
status `COMPLETED`, its adapter files and final resource-log hash are
accounted, and its training storage reservation is released. The scorer also
requires a successful development-only preflight bound to the same training,
adapter, model, data, protocol, tokenizer, and evaluator identities. It loads
the base and adapter under a fresh 10% RAM/VRAM resource monitor before it
opens held-out examples. Before model loading, it acquires a cross-process
Windows file lock at `heldout-scoring.lock`, then rechecks the global access
marker after acquiring the lock. Immediately before the first held-out read,
it creates `heldout-access.started.json` with exclusive-create semantics and
also writes a per-job marker. The global marker prevents races between
different job IDs and blocks all later attempts. If that marker exists, do
not rerun or tune on this split. A catchable failure writes a receipt with
marker state, resource-log identity, and bounded exception detail; preserve
partial predictions. A pre-access failure with no global marker may be
retried only under a new job ID after diagnosis. The held-out file hash may be
checked from its manifest before access.

The only training candidate this revision can score is the admitted
attention-only fit 03:
`WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN`, with manifest under
`C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-fit-03-attention-only`
and adapter/source snapshot under
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\lora-screen-02\\fit-03-attention-only`.
The scorer requires exactly 24 `self_attn` q/k/v/o targets and 540,672
trainable parameters, the current trainer and protocol hashes, and exactly 96
completed optimizer steps. The failed fit attempt 01 and the stale fit 02
identity are not eligible for this revision. Fit 03 must finish and its
training reservation must be released before the development-only scorer
preflight can be admitted.

The scorer pins the reviewed fit-03 trainer SHA-256
`62319402f24721532eeece095a298ffbd47da7852cde2b397589ffb48b3c13cc` and
checks both the run receipt and saved source snapshot against it. It also
checks the exact 24 module names (`self_attn` q/k/v/o at layers 3, 7, 11, 15,
19, and 23), not only the profile label and parameter count. The fit-03
scorer/protocol pair must receive a fresh exact-hash review before training or
inference; changes invalidate that review.

## Fixed arms and inputs

Score the exact 128 held-out cases once, in paired form:

1. A deterministic bounded policy implemented from the visible user prompt
   and visible evidence records only. It must not inspect `gold`, `family`,
   `template_group`, example IDs, or split metadata when deciding.
2. The frozen `Qwen/Qwen3.5-0.8B` base at revision
   `2fc06364715b967f1860aea9cf38778875588b17`.
3. The same base with the adapter produced only by the completed fit 03
   attention-only candidate.

The predictor receives only the system and user messages. The evaluator keeps
the reference output in a separate scoring path and exposes it only after
predictions are sealed. No prompt may contain the family label, gold output,
or split-specific fields. No frontier model call is part of this local screen.

For both neural arms, use the frozen model tokenizer and chat template, greedy
decoding (`do_sample=false`, `num_beams=1`, `max_new_tokens=96`), and identical
prompt bytes. Record exact model, tokenizer, template, adapter, evaluator,
device, dtype, and runtime hashes. The evaluator source hash and Git HEAD are
recorded; the source hash must match the preflight receipt. A single dev-only generation preflight may
select a safe device/dtype before held-out access; if CUDA BF16 is tried, it
must have its own storage reservation and continuous 10% RAM/VRAM monitoring.
If the CUDA attempt fails without breaching a resource floor, that same
preflight falls back to the demonstrated CPU FP32 path. If both paths fail,
stop before opening held-out data. Never change decoding or parsing after
seeing held-out outputs.

The exact screen-02 source (including the evaluator) must pass a fresh
independent exact-hash static review before training or either inference run.
The dataset manifest, model inventory, candidate metadata, train/dev file
hashes, and RTX 5060 Ti UUID are pinned independently in the runner. Before
reading Wrench-owned inputs, resolve the dataset root, model root, inventory,
adapter, add-on runtime, and reservation through junctions/symlinks and require
them to remain under `C:\\wrench-slm-data`. Every manifest-controlled data path
must be relative and resolve within the approved dataset root. Before and
throughout each job, the scorer checks an active
reservation and destination free space. Reserve at least 500,000,000 bytes for
the development preflight and 1,000,000,000 bytes for the one-shot held-out
scoring job. Use reservation IDs
`WRENCH-GATEWAY-SCREEN-02-EVAL-PREFLIGHT-20260927-NN` and
`WRENCH-GATEWAY-SCREEN-02-HELDOUT-20260927-NN`; increment the two-digit suffix
for a diagnosed pre-access retry. These reservations cover the 128 MiB
aggregate output cap, logs, temporary JSON
replacement files, and bounded local runtime scratch. Use a new scratch root
under `C:\\wrench-slm-data\\cache\\gateway-screen-02\\<job-id>`; route Hugging
Face, Torch, XDG, CUDA, Triton, extension-build, and OS temporary paths there.
The development preflight scratch cap is 256 MiB and the held-out scoring
scratch cap is 512 MiB. Resource samples and the final receipt record observed
scratch bytes. A sampled or final cap breach fails the job. These application
checks are not an OS quota, so preserve the full storage reservation for
simultaneous scratch and output growth. Every resource sample, including the
training samples, must identify the pinned GPU and remain above the 10%
RAM/VRAM floors.
Scratch accounting must enumerate entries without following links. Reject
every Windows reparse point, hard-linked file, and unsupported filesystem
entry in the per-job scratch tree; a symlink-only check is insufficient.
When the held-out scorer validates the already-completed development-preflight
receipt, it must verify that resource log using the preflight's 256 MiB cap.
The held-out job's 512 MiB active cap applies only to its own resource samples
and final receipt.

Before hashing or loading base-model or adapter files, pin the complete tree
under retained no-write/no-delete directory handles. Open every regular file
without following reparse points, require one NTFS link, and hash from the
same retained read-only file handle that remains open while Transformers or
PEFT reads the path-based files. Rehash the pinned handles after both loads and
fail closed on sharing violations or identity changes. Load the helper
implementation from bytes matching its source hash fixed in both scorer and
training receipt. Do not fall back to path-only model or adapter verification.

Scratch accounting pins the scratch root before the monitor or workload
starts. It retains every discovered directory handle, denying delete sharing,
until the monitor stops and final accounting finishes. Each sample opens file
handles only for that scan, allows active writes, then closes those file
handles before the next sample. Re-scans must use the same pinned root. This
prevents replacement of already pinned directories between samples. Newly
created entries can still grow or change between samples, so the sampled
scratch cap remains an application monitor, not an OS quota or a bound on
concurrent writers. Serialize every tree scan and its file-handle release.
While the monitor is active, output-budget checks use its latest scratch sample
instead of starting a competing scan. After stopping the monitor, take and
record a fresh final measurement as `runtime_scratch_bytes_at_finalize`, and
include it in `runtime_scratch_peak_bytes` in the receipt summary.

The aggregate per-job output cap covers prediction, resource, marker, lock,
and receipt bytes, including the held-out lock owner's JSON metadata. In-process
code must hold one shared output-budget lock from a fresh aggregate check
through each corresponding append, write, or atomic replacement. This
serializes the main scoring thread with the resource monitor; a check performed
before acquiring the lock is not a reservation. After acquiring the OS-held
out-file lock, recheck the aggregate budget while holding the shared
output-budget lock, then truncate and write the owner metadata under that same
lock. Count the existing lock-file size conservatively when admitting the
replacement metadata.
Before opening the global held-out lock, resolve its parent and lock path under
the approved artifact directory and reject a linked lock file. Resolve the
fixed training resource log and reject a linked child before hashing or
reading it.

The global lock and one-shot marker must be opened through Windows handles
with `FILE_FLAG_OPEN_REPARSE_POINT`. Keep the parent directory handle open
without delete sharing while opening the child, then verify the opened
directory and child handle's final paths, attributes, file identity, and
require the child's NTFS link count to equal one before any write. Keep the
global marker handle open without delete sharing until the held-out job
finishes, so the one-shot claim cannot be replaced during access.
When checking marker or lock size for output admission, use `os.fstat` on the
validated handle; do not resolve, stat, or reopen the path after validation.
The same handle-based child check applies when reading marker hashes in
receipts. Read the user-supplied preflight receipt through a confined,
single-link handle once, bind its location to the validated job ID, and hash
and parse those same bytes. Read the fixed training manifest once through a
confined, single-link handle; use the digest of those parsed bytes in the
development-preflight receipt and held-out result. Require the training
manifest to carry the fit-preflight manifest and resource-log hashes. Read the
training and preflight resource logs
through validated read-only handles once, hash those exact bytes, and parse
those same bytes. Reject any hard-linked file or log, and do not hash and then
reopen by path. A path check made before an ordinary `open` is not sufficient.

Read train/dev inputs once through confined, single-link Windows handles;
verify the pinned length and digest against the same bytes that are parsed.
After writing the global held-out access marker, read the held-out split once
through the same kind of handle and verify its pinned size/hash from that
buffer. Project only prompt fields from this buffer for prediction. Flush and
hash all prediction files before parsing family/gold references from the same
held-out buffer; never reopen the path for the label pass.

The base and adapter arms share one loaded base snapshot to bound memory.
Disable PEFT adapter layers explicitly with its supported context manager for
the base arm, then run the adapter arm with those layers enabled. This prevents
the supposedly frozen base control from inheriting the active LoRA.

Each generation uses a 300-second `max_time` stopping threshold. Transformers
checks this cooperatively during generation, so record actual elapsed wall time
and any partial raw output; a timeout is a failed decision. The 96-token
completion limit is tracked separately from timeouts.
A device/dtype preflight is successful only when both its base and adapted
development generations finish below that threshold. Preserve a timed-out
partial output, reject that candidate, and try CPU only after a non-breaching
CUDA failure; if CPU also times out, stop before held-out access.

## Scoring

Preserve every output, including malformed JSON and timeouts. A strict parser
requires exactly the five schema fields, allowed enum values, a boolean
`retrieve_more`, unique evidence IDs present in the visible records, and no
extra keys. Report per arm:

- exact full-decision accuracy and strict-valid-output rate;
- route accuracy and local, `FRONTIER`, and `ABSTAIN` counts;
- selected-source exactness, invalid-source rate, over-budget rate, and
  authority violations;
- results by the four task families and paired base-vs-LoRA difference;
- wall time, peak RAM/VRAM, prompt and completion tokens, and all failures.

For the 32 synthetic compaction-policy cases, additionally report exact
omitted-record rate, critical hot-evidence recall, case-level preservation of
all hot records, hot-preserving compaction rate, and simulated re-fetch
resolution for each omitted cold ID. Whole-context hot preservation treats a
non-compaction decision (including a rejected invalid output or timeout) as
preserved because the selector has no mutation authority and the runtime
leaves the original context intact unless a valid compaction is accepted. The
empty hot-record set is vacuously preserved.
compaction-only preservation rate has accepted compactions as its denominator;
report its numerator and denominator separately. These are policy-level
metrics and do not establish that an untested production executor follows this
fail-closed contract.

Attempt simulated re-fetch for every omitted cold ID in every accepted
compaction, including hot-dropping compactions. Report total attempts,
resolutions, and unresolved IDs, stratified into hot-preserving and
hot-dropping compactions. Re-fetch simulation looks up the ID in the same
immutable synthetic record snapshot and checks canonical record bytes; it does
not test a live Wrench store. Compute the exact tokenizer-token count of the
canonical full record list and the selected records only after every selected
ID resolves in that snapshot. Report projected and hot-preserving record-token
reduction separately. The unqualified geometric projection can include
hot-dropping compactions, but must be labeled unqualified and never counted as
savings. Invalid, timed-out, non-compaction, and hot-dropping outputs count as
zero in the credited hot-preserving reduction. This records prospective
context reduction, not actual frontier calls or frontier-token savings. Keep
the local selector prompt and completion tokens separate. For aggregate ratios
and evidence recall, report exact numerator/denominator and a 10,000-resample
case-cluster percentile interval with seed `20260927`; use a Wilson interval
for both case-level hot-preservation and hot-preserving compaction rate.
The deterministic arm's prompt and output token counts are tokenizer-equivalent
diagnostics only; they do not represent language-model usage or cost.

Include exact denominators and 95% Wilson intervals for rates. Preserve all
128 cases in each arm's denominator. Show only diagnostic paired uncertainty;
do not call a small synthetic sample a product-level confidence claim.
The paired base-vs-LoRA accuracy difference uses a preregistered percentile
bootstrap with 10,000 paired resamples and seed `20260927`. A selection is
over budget only for prompts with an explicit `Budget: N tokens` field: sum
the pinned tokenizer's no-special-token count for each selected visible record
serialized as canonical sorted-key JSON, and compare that sum with N. Report
the over-budget denominator separately (the budget-bearing cases only).
Invalid or repeated source IDs remain separate safety failures.

The generator's frozen specification implies 104 local labels, 8 frontier
labels, and 16 abstain labels per 128-case split. That mix cannot pass the
95%-local / 5%-frontier product target and is not to be reweighted after
opening the held-out file. Treat this as a bounded schema/learning screen.

## What this evaluation cannot prove

This screen cannot establish local coding completion, all-day engineering,
representative route share, or frontier-token savings. It contains short
synthetic prompts rather than real repository tasks, and it makes no provider
calls. Context/token diagnostics must not be relabeled as frontier usage. The
paired frontier-only and hybrid comparison, actual route share, 95% task
completion, and 95% frontier-token reduction require separately authorized,
outcome-verified held-out engineering tasks and auditable provider usage
receipts. The `localhost:4000` force-mode subroute remains unavailable for
generation until a hard USD cap is recorded.
