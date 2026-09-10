# Pro training V9 abstention repair budget

Prepared 2026-09-10 after V8 restored routine task behavior but failed one
fixed ambiguity gate. This is a small repair phase on top of the V8 adapter. It
does not change release thresholds, external evidence rules, or the router
scope.

## V8 evidence

V8 was trained from V7 with a lower learning rate and 30,026 training rows.
Step 300 restored 175/176 exact development predictions. Every routine case,
task slice, language slice, unsupported case, invalid range, and fixture check
passed. The sole failure was an ambiguous development request with no selected
service: the model emitted a `read_file` call instead of the required explicit
fallback. The selector therefore reported `TRAINED CANDIDATE, QUALITY GATES
FAILED` and V8 was not packaged or scored on external release sets.

The V8 step-300 adapter SHA-256 is
`89305a1b591142076ec221bee5e6a8c19bfdb1f79d6e1c2b13d8faa9e9320c43`.

## V9 data

The directory is `data/pilots/release-generalization-v9`.

- Training rows: 31,050
- Training families: 208
- Training SHA-256: `bbc79b84a734495abdda5d0ade0ba59ae3aff59046465569c4b6d17535f7ee0e`
- Parent V8 train SHA-256: `0e48f61a131ba2247605ebe0e0440155a22f36a9db92f7ac9fde9ad0930308bd`
- Generator SHA-256: `c9d2f59169954fdec10221a179791dd9128a1cfa8408e39fb8190a5c37b2cc76`
- New rows: 1,024 explicit abstention examples in eight fresh wording families
- Development and evaluation: unchanged V8 files
- Dropped duplicates: zero
- Label conflicts: zero
- Cross-split exact inputs and families: zero

The additions cover English and Chinese requests that lack a selected service or
file. They explicitly teach that available resource distractors do not justify
choosing a configuration and that the correct action is the fallback. No
scored prediction or external evaluation row was imported. Preflight passed
with the same 604-token maximum training length, 554-token maximum prompt, and
53-token maximum completion.

## Bounded run

Initialize from `artifacts/model-release/pro-training-v8/checkpoint`, whose
adapter SHA-256 must be
`89305a1b591142076ec221bee5e6a8c19bfdb1f79d6e1c2b13d8faa9e9320c43`.
Reset the optimizer and do not use `--resume-from`. Run the one-step
warm-start diagnostic first and require the expected initializer and
`optimizer_reset: true`.

Run at most 150 optimizer steps with checkpoints at 50, 100, and 150. This is
at most 2,400 presentations. Use learning rate `0.000005`, seed 42, BF16,
microbatch 2, accumulation 8, maximum length 1536, and CUDA allocator fraction
0.55. The shorter budget limits forgetting in the task slices that V8 restored.
The main receipt must show finite losses, completion, all checkpoints, the V9
hashes, and the expected initializer hash.

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v9/train.jsonl `
  --val data/pilots/release-generalization-v9/development.jsonl `
  --output artifacts/model-release/warmstart-diagnostic-v9 `
  --steps 1 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.000005 --seed 42 --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v8/checkpoint

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v9/train.jsonl `
  --val data/pilots/release-generalization-v9/development.jsonl `
  --output artifacts/model-release/pro-training-v9 `
  --steps 150 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.000005 --seed 42 --checkpoint-every 50 `
  --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v8/checkpoint
```

## Selection and release gate

Evaluate steps 50, 100, and 150 on the unchanged 176-case development set and
select only a checkpoint for which every fixed quality gate passes. Rank by
exact rate, validation loss, and earliest step. If no checkpoint passes the
ambiguity gate, stop with V8 preserved as the best routine candidate.

If a V9 checkpoint passes, package it, rerun context-development-v2 and the
clean offline CUDA verifier, then author fresh challenge-v4 and sealed-v4. The
V3 sets are retired because they informed V8 and must not be reused. Freeze
fresh manifests before model scoring and retain gold fixture receipts.

The final weight decision still requires every fixed threshold, raw output,
actual outcome, language and per-kind slice, package checksum, clean load,
model card, dependency freeze, licensing review, measured resources, and
inference instructions. If V9 passes development but fresh external evidence
fails, keep `TRAINED CANDIDATE` and document the failure. Do not create an
unbounded correction loop. Router integration and deployment remain deferred.
