# Pro training V5 context-correction budget

Prepared 2026-09-09 after V4 completed all original development gates but failed
the packaged context guard. This is a bounded correction phase. The original
release thresholds, prompt formatter, tokenizer, base revision, inference
contract, and independent test manifests remain unchanged.

## Evidence requiring this phase

The V4 step-150, step-300, and step-450 packages all passed the unchanged
176-case development set at 176/176 exact, including all routine outcomes,
abstentions, languages, and fixture-integrity checks. The development selector
therefore chose step 450 by lowest validation loss, adapter SHA-256
`a32eb58bb6b5600e1b52fbd26b93ff524bf0efc1bfd8b79201530f5d17a52b90`.

The exact packaged step-450 artifact then scored only 29/37 on
`context-development-v1`. Step 150 scored 33/37 and step 300 scored 31/37 on
the same guard. Failures are concentrated in minimal or reordered tool context,
especially search, Git status, and health. The package loader, base checksum,
tokenizer, and runtime all completed successfully, so this is treated as a model
generalization failure. The original context guard is now retired as development
evidence because it informed this correction. It must not be presented as an
independent test after V5 training.

## Data

`data/pilots/release-context-correction-v5` retains the complete V4 training
corpus and adds authored context-grounding variations. It contains 20,554 train
rows in 100 training families. Its training SHA-256 is
`be83cbfb2547488dc04351f0bcf446f3715322d6d2389d6ae8beff9f828d2606`.

The additions vary tool order, sole-tool schemas, minimal contexts, stale
selections, empty resources, and explicit instructions to use the available
schema. Search, Git status, health, config, line, Git log, and draft examples are
included. No row from `context-development-v1`, the sealed evaluation, or the
independent challenge was imported. Development and sealed evaluation files are
byte-identical to V4. Preflight passed with maximum full training length 604
tokens, maximum prompt 554 tokens, and maximum completion 53 tokens.

The fresh context guard is
`data/pilots/context-development-v2/development.jsonl`, 37 cases in 13 families,
SHA-256 `fdbe1b5dfff66f9c59f11659a075fdd3b8a50c2b6602c547a7b46b34025bb766`.
It uses new generated values and prompts and does not import V1 probe rows. It is
a development guard, not a sealed release test. The required guard is at least
95% exact with correct actual outcomes and a passing packaged quickstart. All
37 cases remain in the denominator.

## Initializer and budget

- Initialize from the completed V4 step-450 adapter at
  `artifacts/model-release/pro-training-v4-resumed-v1/checkpoint`.
- Verify the initializer adapter hash before launching:
  `a32eb58bb6b5600e1b52fbd26b93ff524bf0efc1bfd8b79201530f5d17a52b90`.
- Reset the optimizer deliberately. This is a new data phase, not an exact
  resume. Do not pass `--resume-from`.
- Run a one-step warm-start diagnostic first, at most 16 presentations, in its
  own output directory. It proves the initializer and contract load; it is not a
  candidate.
- Main run: at most 300 optimizer steps, microbatch 2, accumulation 8, constant
  learning rate `0.00001`, seed 42, BF16, maximum sequence length 1536.
- Save checkpoints at steps 100, 200, and 300. This permits at most 4,800
  example presentations and three development candidates.
- Cap the CUDA allocator at 55% of the RTX 5070 Ti. Allow at most 60 minutes for
  the main run including validation and checkpoint writes. Use no cloud calls and
  no automatic retries.
- Selection remains highest exact rate on the unchanged 176-case development
  set, then lowest validation loss, then earliest step. Do not use the retired
  V1 context score to select a checkpoint.

The V5 phase is successful only if it improves the fresh context guard without
regressing the fixed original development gates. A completed process or lower
training loss does not establish success.

## Commands

Run from the repository root after confirming no competing GPU process:

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-context-correction-v5/train.jsonl `
  --val data/pilots/release-context-correction-v5/development.jsonl `
  --output artifacts/model-release/warmstart-diagnostic-v5 `
  --steps 1 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.00001 --seed 42 --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v4-resumed-v1/checkpoint

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-context-correction-v5/train.jsonl `
  --val data/pilots/release-context-correction-v5/development.jsonl `
  --output artifacts/model-release/pro-training-v5 `
  --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.00001 --seed 42 --checkpoint-every 100 `
  --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v4-resumed-v1/checkpoint
```

Require the diagnostic receipt to be completed with the expected initializer,
formatter, tokenizer, and `optimizer_reset: true` before starting the main run.
The main receipt must report `status: completed`, 300 steps, 4,800 presentations,
finite losses, all three checkpoints, and the V5 train/validation hashes.

## Evaluation sequence

First evaluate every V5 checkpoint on the unchanged original development set.
Use new output directories and execute real disposable fixtures:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-context-correction-v5 --checkpoint artifacts/model-release/pro-training-v5/step-000100 --output artifacts/model-release/v5-development-step100 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-context-correction-v5 --checkpoint artifacts/model-release/pro-training-v5/step-000200 --output artifacts/model-release/v5-development-step200 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-context-correction-v5 --checkpoint artifacts/model-release/pro-training-v5/checkpoint --output artifacts/model-release/v5-development-step300 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_select.py `
  --training-run artifacts/model-release/pro-training-v5 `
  --evaluations artifacts/model-release/v5-development-step100 artifacts/model-release/v5-development-step200 artifacts/model-release/v5-development-step300 `
  --output artifacts/model-release/selection-v5
```

Do not select a checkpoint if any original development gate fails. Then package
the selected checkpoint and run the fresh context guard through the packaged
runtime:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/package_weights.py `
  --checkpoint <selected-checkpoint-from-selection-v5> `
  --output artifacts/model-release/package-selected-v5 `
  --license artifacts/model-release/licensing-v1/LICENSE-QWEN
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py `
  --data data/pilots/context-development-v2 `
  --package artifacts/model-release/package-selected-v5 `
  --base-path artifacts/model-release/base-dependency-v1 `
  --output artifacts/model-release/v5-package-context-development --execute
```

The fresh guard must reach at least 35/37 exact predictions and outcomes. Keep
raw outputs for every case. A passing original development set with a failed
fresh context guard remains `TRAINED CANDIDATE`, not release-ready.

## If V5 passes the guards

Run the corrected clean-environment verifier on the exact package. Then, and only
then, run the frozen 66-case independent challenge and 440-case sealed evaluation
on that same package and base dependency. Use the existing release thresholds,
keep all cases in the denominators, and retain package/runtime/adapter hashes.
If either frozen set informs another training change, retire that set and create
a fresh independent set before making a new release decision.

The final package still needs a complete model card, lineage, measured CUDA and
process resources, dependency freeze, licensing review, and final checksum after
documentation edits. Passing V5 development and context guards does not by itself
authorize public upload or production deployment.

## If V5 fails

Preserve all receipts and identify whether the failure is a model error, label
error, fixture error, or packaging/runtime mismatch. Do not lower the 95% context
guard, remove difficult examples, or treat fallback conversion as a correct
prediction. If another training phase is justified, create a new versioned data
directory and budget document. Keep the sealed evaluation and independent
challenge untouched.
