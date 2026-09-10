# Training repair and future-run handoff

Updated: 2026-09-10

The V16 training correctness defects have been repaired and verified by the
V21 run. The current release artifact is complete at
`artifacts/model-release/package-selected-v21`. Do not start another run just
to improve a green score. Start a new run only when a new, observed failure or
new model scope justifies it.

## What the repair fixed

The V16 audit found two different classes of problems:

1. Many rows were semantically unprovable from public input. Examples included
   unresolved `__PORT__` values, hidden draft content, decoy-resource identity
   mismatches, target paths that disagreed with the selected file, and
   invalid-range labels that depended on hidden fixture details.
2. The sequential loader presented a grouped prefix. The V16 checkpoints saw
   almost only invalid-range rows even though the full dataset contained other
   task kinds.

The repaired V17 through V21 generators put all required values in public
context, made resource identity explicit, disclosed file length for boundary
tasks, and built a deterministic mixed stream. V21's semantic audits report
zero errors and zero warnings. Its exposure receipt reports every task kind and
both languages at every selectable checkpoint, with no repeated rows before the
stream consumed the corpus.

The old audit remains at [TRAINING_CORRECTNESS_AUDIT.md](TRAINING_CORRECTNESS_AUDIT.md).
It is historical evidence and should not be edited to make the V21 result look
cleaner.

## Current reproducibility anchors

- Dataset: `data/pilots/release-generalization-v21`
- Train SHA-256: `7734344c4f5097eee9aaf7efaced62727a32545a8103d628af239471026e1c30`
- Formatter SHA-256:
  `3c3d37ec3481da3bedc4f4148c20699c55b3358566e2f253a4caac7b2c4e3ade`
- Base revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Initial adapter SHA-256:
  `a15d22b2f30287a1ccc26100c4e0e552f0516c8d05a8639bbbf07ee3be2e0fda`
- Selected adapter SHA-256:
  `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`
- Run receipt: `artifacts/model-release/pro-training-v21/run.json`
- Exposure receipt: `artifacts/model-release/audit-v21-exposure.json`
- Selection receipt: `artifacts/model-release/selection-v21/selection.json`

The run used 300 optimizer steps, microbatch 2, accumulation 8, learning rate
2e-6, seed 42, and a reset optimizer. It completed 4,800 presentations and
saved checkpoints at steps 100, 200, and 300. Step 200 was selected after all
three checkpoints scored 176/176 on development.

## If a new run becomes necessary

Treat it as a new versioned experiment. Do not overwrite V21 data, receipts,
the selected package, or its final evaluation. Do not train on a scored holdout
that has informed a previous correction.

### 1. Write the hypothesis

State the observed failure, the smallest data or formatter change that should
address it, the expected slice to improve, and the risk of regression. Decide
whether the pinned base or V21 adapter is the appropriate initializer. A newer
adapter is not automatically better.

### 2. Author a new dataset

Create a new generator and a new directory under `data/pilots`. Keep train,
development, and evaluation families disjoint. For every row, verify:

- The selected target path, URL, marker, or content is visible in public input.
- Every port is concrete and consistent across context, command, and fixture.
- Resource selection is by identity, not list position.
- Valid inclusive ranges are paired with zero or negative, reversed, and
  beyond-EOF cases. Public file length is available where it is required.
- Natural requests and explicit fallback instructions are varied separately.
- English and Chinese cases are balanced in each task slice where both are
  supported.

Run the semantic audit and structural preflight before GPU time:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/audit_training_data.py `
  --data data/pilots/NEW_VERSION `
  --split train `
  --output artifacts/model-release/audit-NEW_VERSION-semantic-train

.venv\Scripts\python.exe -X utf8 scripts/release_preflight.py `
  --data data/pilots/NEW_VERSION `
  --output artifacts/model-release/data-preflight-NEW_VERSION
```

Require zero semantic errors and warnings, complete labels, no duplicate
inputs, and complete token budgets. Run executable gold checks against the
fixtures before model inference:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_gold_check.py `
  --data data/pilots/NEW_VERSION `
  --split evaluation `
  --output artifacts/model-release/gold-NEW_VERSION
```

### 3. Freeze exposure and training

Use the mixed-stream generator and record the exact ordered-ID digest and
counts at every proposed checkpoint. At batch size 2 and accumulation 8,
steps 100, 200, and 300 present 1,600, 3,200, and 4,800 examples. Reject the
run plan if any required kind or language is absent from a selectable
checkpoint. Keep the optimizer reset when warm-starting an adapter unless the
experiment explicitly studies resume semantics.

Run only the declared bounded budget. Preserve the run receipt, source
snapshots, contracts, losses, and at most three weight-bearing snapshots per
active trainer:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/NEW_VERSION/train.jsonl `
  --val data/pilots/NEW_VERSION/development.jsonl `
  --output artifacts/model-release/pro-training-NEW_VERSION `
  --steps 300 `
  --max-length 1536 `
  --batch-size 2 `
  --accumulation 8 `
  --learning-rate 2e-6 `
  --seed 42 `
  --checkpoint-every 100 `
  --initialize-adapter artifacts/model-release/package-selected-v21/weights
```

The command is a template only. Replace every uppercase path and record the
actual arguments before execution. Monitor finite loss, validation loss,
exposure, CUDA allocation, and free disk. Stop and preserve evidence if any
one becomes unexplained or non-finite.

### 4. Evaluate and select

Evaluate every declared checkpoint on the unchanged development split. Select
using the frozen rule: highest exact rate, then lowest validation loss, then
earliest step. Never select from final holdout results. Run the exposure audit
against the exact training stream and retain its receipt.

Package only the selected checkpoint. Verify adapter, tokenizer, formatter,
base, and runtime hashes before external scoring. If a package edit is made,
rebuild its checksum manifest and rerun the clean verifier.

### 5. Freeze a fresh holdout

Author a new context and final evaluation set only after the candidate is
frozen. Use fresh families, paths, values, and wording. Include context
reordering, decoys, quoting, Unicode, long inputs, invalid boundaries, and
unsupported requests. Run preflight and gold checks before scoring. If the
holdout result informs any correction, retire it and author another version.

The current V21 independent evidence is:

- Final holdout: 440/440 exact, 280/280 routine, 160/160 fallback.
- Fresh context suite: 220/220 exact, 140/140 routine, 80/80 fallback.
- Both suites: all task and language gates true, zero filesystem changes.

These are release receipts, not training inputs.

## Storage and cleanup

The model and checkpoint ceiling is 5,000,000,000 bytes. Before a run, count
base weights, adapter files, optimizer states, native snapshots, and temporary
copies. Reserve space for the next atomic checkpoint. Retain the pinned base,
the selected package, the latest recoverable state, and no more than three
active trainer snapshots. Delete superseded weight files only after their
receipts and hashes are preserved.

V21 currently retains 4,447,301,853 model and checkpoint bytes. The retained
weight-bearing paths are `base-dependency-v1`, `package-selected-v20`,
`package-selected-v21`, and V21 `step-000100`, `step-000200`, and final
`checkpoint`. The separate `clean-env-v21` environment is retained for clean
verification and is dependency storage, not model or checkpoint storage.

Never track weights in Git. Confirm with `git ls-files` before staging any code
change. The sidecar trainer must remain stopped unless its retention and budget
behavior have been re-audited.

## Release boundary

V21 is ready as a local adapter package for the authored Wrench-Pro scope. It
does not establish production-service reliability, router savings, cloud
failover, arbitrary shell safety, broad language coverage, CPU performance, or
clinical use. Any merge, quantization, conversion, or runtime change requires
new checksums and a complete evaluation.
