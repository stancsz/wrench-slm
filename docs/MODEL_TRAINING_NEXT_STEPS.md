# Wrench-Pro training and weight-release history

> Current operator instructions: [MODEL_RELEASE_HANDOFF.md](MODEL_RELEASE_HANDOFF.md)
> and [TRAINING_REPAIR_HANDOFF.md](TRAINING_REPAIR_HANDOFF.md). The V21
> package is ready for release within the declared weight scope. Do not start a
> new training run without a new observed hypothesis and versioned evaluation.

Prepared: 2026-09-09. This file retains the earlier V4 through V12 execution
history for provenance. It is not the current run plan. Current V21 evidence is
recorded in [MODEL_RELEASE_PROGRESS.md](MODEL_RELEASE_PROGRESS.md) and
[goal.md](../goal.md).

## 1. Objective and immediate next step

Finish training Wrench-Pro, demonstrate useful model behavior on independent
tasks, and package usable weights for release. Router integration, gateway
changes, cloud comparisons, Flash training, public upload, and service deployment
are deferred. The V21 run and package now satisfy the weight-release definition
of done; the historical commands below are retained for audit context only.

The original V4 resume instructions below are historical. Do not resume V4 or
V12. V21 is the current selected artifact and has weight-release approval. If a
future correction is needed, follow TRAINING_REPAIR_HANDOFF.md and create new
versioned data and holdouts.

This document is an execution guide for a later session. The commands below have
not been run unless explicitly identified as completed evidence. All example
paths are relative to the repository after the initial `Set-Location` command.
Use fresh output directories and retain failed or partial runs.

## 2. Exact pause state

Training and development-evaluation Python processes were stopped after step
300 was saved. Their absence was verified. A trusted local CPU load of
`trainer_state.pt` succeeded and confirmed step 300, 4,800 presentations,
optimizer state, model state, CPU/CUDA RNG state, and the dataset contract.

| Item | Recorded state |
| --- | --- |
| Original V4 run | `artifacts/model-release/pro-training-v4` |
| Recovery checkpoint | `artifacts/model-release/pro-training-v4/step-000300` |
| Target | 450 total optimizer steps, 7,200 total presentations |
| Saved progress | 300 steps, 4,800 presentations |
| Remaining from checkpoint | 150 steps, 2,400 presentations |
| Full trainer-state SHA-256 | `7c95779293056f948e7a7bb01ed6b850d362aa3a5006b62e51a71d31c85b7837` |
| Step-300 adapter SHA-256 | `a05ee69a2ccaf3835a511d50c91d06b681003dcd03cddd14cb1fcbb7e4b198e0` |
| Pause receipt | `artifacts/model-release/pro-training-v4/pause_receipt.json` |
| Interrupted evaluation | `artifacts/model-release/v4-development-step150` |
| Partial evaluation result | 110/110 exact of 176 assigned tasks; incomplete, ineligible for selection |

The original `run.json` files were preserved. They may still say `started` or
`running` because terminating a process does not execute its final receipt
writer. The pause receipt explains this. Do not interpret those stale status
strings as live processes, and do not interpret the partial score as 176/176.
Any logged training steps beyond 300 were not part of this saved checkpoint and
must be replayed during exact resume.

## 3. Model and runtime contract

| Setting | Required value |
| --- | --- |
| Base | `Qwen/Qwen2.5-0.5B-Instruct` |
| Base revision | `7ae557604adf67be50417f59c2c2f167def9a775` |
| Base weight SHA-256 | `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe` |
| Adapter | PEFT LoRA, rank 16, alpha 32, dropout 0.05 |
| Target modules | q/k/v/o projections and gate/up/down projections |
| Trainable parameters | 8,798,208 |
| Training precision / attention | BF16 / SDPA |
| Tokenizer | Original pinned Qwen tokenizer, vocabulary, special tokens, and chat template |
| Formatter | `wrench/dataset.py` |
| Formatter SHA-256 | `3c3d37ec3481da3bedc4f4148c20699c55b3358566e2f253a4caac7b2c4e3ade` |
| Input / output budgets | 1,536 input tokens / 192 generated tokens |
| Inference | Greedy decoding; raw output retained; strict validation reported separately |
| Contract | One canonical tool/args JSON object or literal `ROUTER_FALLBACK` |

The model sees only the user prompt and public context, including actual tool
schemas, resources, and prior selections. It must not see gold calls, expected
answers, fixture contents, task labels, or evaluation metadata as hidden inputs.
The package returns proposals and executes no generated tools.

The verified local training environment is `.venv/Scripts/python.exe`, Python
3.14.0, torch 2.9.1+cu128, transformers 4.57.1, peft 0.20.0, tokenizers 0.22.1,
and safetensors 0.6.2. Hardware is an RTX 5070 Ti with 16 GB VRAM on Windows.
The training allocator is capped at 55% of device memory. V3's observed peak
PyTorch allocation was 6,593,259,008 bytes; this is not the complete GPU footprint
and excludes other applications. Preserve headroom for the desktop.

## 4. Data and evidence inventory

### Current training data

`data/pilots/release-boundary-v4` contains 6,084 training rows in 100 training
families, equally divided between English and Chinese. Its train SHA-256 is
`61643804bae59e6b70fd194fbeac65014eca788402fd62345e8d0bcbb0e5f4ac`.

V4 retains all 4,548 V3 rows. It adds 768 unsupported-request examples from 32
new prompts and 768 range examples from 12 wordings with positive, zero,
negative, and reversed bounds. Positive range labels have real fixture lines.
The expansion addresses observed development failures and the earlier corpus's
four distinct unsupported-request prompts. It contains no copied development,
sealed evaluation, or independent challenge rows.

| Dataset | Size and role | Receipt or hash |
| --- | --- | --- |
| `release-authoring-v1` | 1,408 initial train rows / 44 families | Its manifest and `data-preflight-v1` |
| `release-context-v2` | 3,076 train rows / 44 families, context contrast pairs | Train `54c46aa4b1211b490d4b66d20a1757dc8b2beafccce36cbb950e92d91caf58ac` |
| `release-literal-v3` | 4,548 train rows / 56 families, literal-copy corrections | Train `ee7a7d80fe6e3b3481f81d6888855f816d3bae422de2a8ef9efa7285b1aafa34` |
| V4 development | 176 rows / 22 families, unchanged across V1 through V4 | `f7ba4d4cf518bbd40612df0851c608de6fff72f6506a4ee508ae1e39409e8d94` |
| Sealed release evaluation | 440 rows / 22 families, never model-scored | `7c09249d94f446b0b9ca9a026816a16e25fc0cf99f0e32eedda41827c01763c6` |
| `context-development-v1` | 37 development probes / 13 families | `4574c0f5eb657cf994f03e6dc31664c1ef98782492c5c209b523782ea709d8ad` |
| `independent-challenge-v1` | 66 independently authored cases / 60 families, never model-scored | `2393a157a8a85f21bdf1189e6e38988fbe27e0bf763ef199e65257bca4f32ad8` |

All data here is authored. Shared fixture generators, limited wording diversity,
and repeated development use limit the evidence. Exact-input and family
separation are necessary but do not establish production representativeness.
The 37 context probes are development data, including after the V3 package run.

`data-preflight-v4` passed schema, checksum, split, and length checks. Its maximum
full training sequence is 588 tokens, so no target truncation is needed. Twelve
representative new range families passed real fixture tests, including rejection
of full-file reads when a precise interval was requested. The independent
challenge's 42 positive gold calls passed fixture checks; its 24 fallback labels
have a recorded semantic review. Those checks did not invoke the model and are
not independent human validation or model-quality evidence.

### Completed model results

| Candidate | Complete development result | Interpretation |
| --- | --- | --- |
| Unchanged pinned base | 4/176 exact | Baseline on this custom tool-call contract, not general intelligence |
| Original 150-step pilot | 99/176 exact; 83/112 routine exact | Not release-ready |
| V1 selected step 300 | 150/176 exact | Release gates failed |
| V2 selected step 400 | 173/176 exact; 110/112 routine exact | Two draft-copy errors and one invalid-range error |
| V3 step 100 | 165/176 exact; 112/112 routine exact and outcomes | Abstention failures |
| V3 selected step 200 | 166/176 exact; 112/112 routine exact and outcomes | Eight unsupported and two invalid-range failures |
| V3 step 300 | 164/176 exact; 112/112 routine exact and outcomes | Abstention failures |
| V3 packaged step 200, context probes | 36/37 exact and outcomes | One invalid Chinese search call after tool reordering; quickstart passed |
| V4 step 150 | 110 correct out of 110 completed, of 176 assigned | Interrupted; no final metric or selection eligibility |

V3 selection receipt: `artifacts/model-release/selection-v3/selection.json`.
The V4 initializer is V3 step 200, adapter SHA-256
`11cee4f2f1f7cd991be01343bb88f96676c86d14b1c902a0b43fb578f47bd15f`.
V4 began with a fresh optimizer. Resuming V4 must restore its saved optimizer,
not reset it again.

## 5. Pre-resume checks

Run from PowerShell:

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'
git status --short
Get-Content artifacts/model-release/pro-training-v4/pause_receipt.json
Get-Content artifacts/model-release/pro-training-v4/step-000300/training_metrics.json
Get-FileHash artifacts/model-release/pro-training-v4/step-000300/trainer_state.pt -Algorithm SHA256
Get-FileHash data/pilots/release-boundary-v4/train.jsonl -Algorithm SHA256
Get-FileHash wrench/dataset.py -Algorithm SHA256
nvidia-smi
```

Match the hashes above and inspect the checkpoint contract. Verify no prior
training/evaluation process has been started by another session. Do not kill
unrelated Python processes. Do not regenerate the existing versioned datasets
or overwrite root `data/train.jsonl`, `val.jsonl`, or `held_out.jsonl`.

The full suite passed 136 tests before the V4 data additions. The 12 new boundary
fixture tests passed separately. These are not yet a single observed 148-test
full-suite result. Before resuming after any code changes, run:

```powershell
.venv\Scripts\python.exe -X utf8 -m pytest tests/test_sft.py tests/test_release.py tests/test_release_context.py tests/test_release_boundaries.py tests/test_weight_package_verifier.py -q
ruff check scripts/pilot_train.py scripts/release_eval.py scripts/release_select.py scripts/release_boundary_data.py scripts/package_weights.py scripts/verify_weight_package.py wrench/sft.py wrench/release_eval.py wrench/weight_inference.py
```

If data or tokenizer files changed, stop and investigate the mismatch. Exact
resume deliberately rejects contract changes. Use a separately budgeted new
phase for changed data; do not bypass the equality check. Source snapshots for
the original run are under `pro-training-v4/source`.

## 6. Resume V4 to total step 450

The output directory below must not exist. If it exists, inspect its receipt and
process state first. Reuse completed work or choose a new versioned output only
after identifying why another attempt is needed.

```powershell
.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-boundary-v4/train.jsonl `
  --val data/pilots/release-boundary-v4/development.jsonl `
  --output artifacts/model-release/pro-training-v4-resumed-v1 `
  --steps 450 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.00002 --seed 42 --checkpoint-every 150 `
  --gpu-memory-fraction 0.55 `
  --resume-from artifacts/model-release/pro-training-v4/step-000300/trainer_state.pt
```

`--resume-from` takes the full trusted `trainer_state.pt` file, not the adapter
directory. Omit `--initialize-adapter`: the two options are mutually exclusive.
The saved state restores weights, optimizer, RNG, and data-iterator position.
This executes steps 301 through 450 and saves `checkpoint/` in the new run.

Keep microbatch, accumulation, learning rate, seed, formatter, base, and dataset
unchanged. Monitor `training_history.jsonl`, process exit, and `run.json`.
Non-finite gradients/loss are failures. A log message or low loss is not proof of
completion. Require `status: completed`, total steps 450, 7,200 presentations,
final adapter/config/tokenizer/contract/metrics, and full trainer state.

The recorded V4 budget is 450 total steps, local GPU only, no automatic retries,
and at most 60 minutes of training/validation/checkpoint work. Count elapsed
work across the original and resumed segments; the resumed duration field alone
does not include the earlier segment. Do not count the user's pause as compute.
If a run stalls or runs out of memory, preserve receipts and recover from a
verified checkpoint. Never blindly start a duplicate process.

## 7. Assemble the three eligible checkpoints for comparison

The current selector requires all checkpoints to share the training-run parent
directory. Exact resume produces only the remaining checkpoint, so copy the two
already saved checkpoint directories into the resumed run after it completes.
These are copies for comparison, not new training. Preserve the originals.

```powershell
Copy-Item -LiteralPath artifacts/model-release/pro-training-v4/step-000150 -Destination artifacts/model-release/pro-training-v4-resumed-v1 -Recurse
Copy-Item -LiteralPath artifacts/model-release/pro-training-v4/step-000300 -Destination artifacts/model-release/pro-training-v4-resumed-v1 -Recurse
New-Item -ItemType Directory -Path artifacts/model-release/pro-training-v4-resumed-v1/lineage
Copy-Item -LiteralPath artifacts/model-release/pro-training-v4/run.json -Destination artifacts/model-release/pro-training-v4-resumed-v1/lineage/original-run.json
Copy-Item -LiteralPath artifacts/model-release/pro-training-v4/pause_receipt.json -Destination artifacts/model-release/pro-training-v4-resumed-v1/lineage/pause-receipt.json
```

Run these copy commands once into absent destinations. Verify copied adapter
hashes against the originals, especially the step-300 hash in this document.
Also retain V3's selection receipt and the V4 initializer identity in the final
training history. Do not describe a copied checkpoint as created by the resumed
segment. The selector will use the completed resumed receipt plus the unchanged
checkpoint contracts and their original step metrics.

## 8. Complete development evaluation and checkpoint selection

The interrupted step-150 evaluation has no evaluator resume support. Keep it as
a partial diagnostic and rerun all 176 cases into a new directory. Do not append
to its predictions or score only the remaining cases. Sequential evaluation is
the default; finish training first to avoid GPU contention in measurements.

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-boundary-v4 --checkpoint artifacts/model-release/pro-training-v4-resumed-v1/step-000150 --output artifacts/model-release/v4-development-step150-complete-v1 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-boundary-v4 --checkpoint artifacts/model-release/pro-training-v4-resumed-v1/step-000300 --output artifacts/model-release/v4-development-step300-complete-v1 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-boundary-v4 --checkpoint artifacts/model-release/pro-training-v4-resumed-v1/checkpoint --output artifacts/model-release/v4-development-step450-complete-v1 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_select.py `
  --training-run artifacts/model-release/pro-training-v4-resumed-v1 `
  --evaluations artifacts/model-release/v4-development-step150-complete-v1 artifacts/model-release/v4-development-step300-complete-v1 artifacts/model-release/v4-development-step450-complete-v1 `
  --output artifacts/model-release/selection-v4
```

Every evaluation must have `status: completed`, all 176 unique task IDs, and a
summary. A zero process exit indicates evaluation completion, not quality pass.
Inspect `model_quality_passed` and each gate. Selection uses highest development
exact rate, then lowest validation loss, then earliest step. Compare all three
planned checkpoints, including weak ones. Do not select on the sealed tests.

## 9. Fixed quality gates and interpretation

The authoritative protocol is [MODEL_RELEASE_PROTOCOL_V1.md](MODEL_RELEASE_PROTOCOL_V1.md).

| Gate | Required observation |
| --- | --- |
| Raw protocol | At least 99.5% schema-valid raw calls or explicit model abstentions |
| Routine exact arguments | At least 95% exact tool and complete arguments |
| Real routine outcomes | At least 95% correct results in disposable fixtures |
| Useful coverage | At least 70% correct useful predictions on supported tasks |
| Supported task/language slices | At least 90% exact in each supported kind and EN/ZH routine slice |
| Ambiguity | At least 95% correct explicit abstention |
| Unsupported, unavailable tools, invalid bounds | 100% correct explicit abstention in each category |
| Execution boundary | Zero unexpected fixture filesystem changes |

Rejecting an invalid model output and converting it to fallback is still a model
failure. Do not count an input-budget rejection as correct abstention. A command
exit code or JSON syntax alone does not establish task success. Range outcomes
must match the requested lines exactly, and draft bodies must match completely.

Report all cases, raw outputs, invalid reasons, exact calls, real outcomes,
fallback counts, and per-language/per-kind results. Retain descriptive Wilson
intervals and the existing family-cluster bootstrap with 2,000 resamples and
seed 20260909. Small authored sets do not prove broad production reliability.

The separate context-development guard requires at least 95% exact predictions
and a passing quickstart. Its generic summary contains false gates for absent
task kinds, because it is not the balanced 11-kind release set. Interpret that
guard separately, but report all actual schema failures. A known schema or tool
order weakness still needs explicit resolution or an evidence-backed scope
decision; do not silently discard the failed context case.

## 10. Export the selected candidate and check context behavior

Only proceed toward independent release testing if the selected checkpoint
passes the fixed development gates. Packaging for diagnosis is allowed while
it remains clearly labeled `TRAINED CANDIDATE`.

```powershell
$selection = Get-Content artifacts/model-release/selection-v4/selection.json | ConvertFrom-Json
$selectedCheckpoint = $selection.selected.checkpoint
.venv\Scripts\python.exe -X utf8 scripts/package_weights.py `
  --checkpoint $selectedCheckpoint `
  --output artifacts/model-release/package-selected-v4 `
  --license artifacts/model-release/licensing-v1/LICENSE-QWEN
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py `
  --data data/pilots/context-development-v1 `
  --package artifacts/model-release/package-selected-v4 `
  --base-path artifacts/model-release/base-dependency-v1 `
  --output artifacts/model-release/v4-package-context-development --execute
```

The package evaluator loads `_wrench_runtime` from the checksummed package,
including its tokenizer and inference settings. This path was exercised on the
V3 package. Verify the adapter hash matches the selected checkpoint and retain
the package-manifest hash in each receipt.

The existing package is an adapter plus an exact base dependency, not a merged
standalone model. Its `weights/` directory includes adapter configuration,
tokenizer files, `added_tokens.json`, `chat_template.jinja`, and training contract.
Do not omit those tokenizer files. Do not ship optimizer state as release weights.

## 11. Clean-environment load and resource checks

The separate environment `artifacts/model-release/clean-env-v1` already exists,
with system-site packages disabled. Its full dependency freeze is
`artifacts/model-release/clean-env-v1-requirements.txt`. An explicit copied base
dependency is at `artifacts/model-release/base-dependency-v1`.

```powershell
.venv\Scripts\python.exe -X utf8 scripts/verify_weight_package.py `
  --package artifacts/model-release/package-selected-v4 `
  --python artifacts/model-release/clean-env-v1/Scripts/python.exe `
  --base-path artifacts/model-release/base-dependency-v1 `
  --output artifacts/model-release/v4-clean-cuda --device cuda
```

This uses a fresh offline cache, disables user site and external Python paths,
loads the package in a separate interpreter, and requires two correct quickstart
predictions. It records startup, full-output latency, process-tree RSS, and CUDA
allocated/reserved peaks. Run with the GPU training/evaluation jobs stopped.
If advertising CPU support, repeat with `--device cpu` and a different output.
CPU results do not replace CUDA quality evaluation or establish CPU latency.

The old `package-verifier-diagnostic-v1` RAM measurement sampled only the Windows
launcher and is invalid. Use the corrected verifier, which includes descendant
interpreters. Its V2 diagnostic measured 3,362,562,048 bytes of process-tree RSS
on the older V1 package; do not copy that number as the new model's requirement.
RSS sums can double-count shared pages. PyTorch peaks exclude other applications.

## 12. Independent evaluation on the exact package

Do not run these commands merely because a checkpoint loads. First satisfy the
development, context, and quickstart requirements and freeze the package hash.
Confirm the test manifests still match the hashes in section 4 and that neither
test has been used for training or candidate selection in another session.

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py `
  --data data/pilots/independent-challenge-v1 --split evaluation `
  --package artifacts/model-release/package-selected-v4 `
  --base-path artifacts/model-release/base-dependency-v1 `
  --output artifacts/model-release/v4-package-independent-challenge --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py `
  --data data/pilots/release-boundary-v4 --split evaluation `
  --package artifacts/model-release/package-selected-v4 `
  --base-path artifacts/model-release/base-dependency-v1 `
  --output artifacts/model-release/v4-package-sealed-release --execute
```

Require all 66 challenge cases and all 440 sealed cases, their expected hashes,
matching adapter identity, completed receipts, and the applicable unchanged
gates. The release set contains 280 supported and 160 fallback cases; the
challenge has 42 supported and 24 fallback cases. Keep every assigned case.
Inspect failures even if an aggregate threshold passes.

These tests use real disposable file, Git, search, and loopback HTTP fixtures.
Writes are draft-only. Concurrent GPU timings from earlier development runs
must not be presented as isolated package performance measurements.

## 13. If a gate fails

Keep the status `TRAINED CANDIDATE` or `NOT READY`, preserve artifacts, and name
the failing gate and closure criterion. Do not lower thresholds after results,
remove difficult tasks, substitute validator fallbacks for correct predictions,
or add task-ID/wording-specific deterministic answers.

For a new training phase, first inspect raw predictions against public inputs,
gold labels, tool schemas, and fixture outcomes. Separate model errors from
bad labels or test-harness defects. Fix a verified harness defect with a regression
test and a new evaluation output; preserve the failed receipt and explanation.

Likely areas to inspect from existing evidence are unsupported-request breadth,
zero/negative/reversed line bounds, literal quoted/newline copying, stale prior
selections, missing tools, and tool-order sensitivity. New examples should vary
semantics, paths, numbers, payloads, and available context, while keeping positive
contrast cases. Retain successful task coverage to detect regressions.

Before any V5 training, write a new budget document with data provenance,
split-family rules, hashes, initializer, optimizer choice, steps, compute cap,
checkpoint schedule, selection rule, and stopping conditions. Use a new dataset
directory. `--initialize-adapter` means a deliberate new phase with a fresh
optimizer; `--resume-from` means the exact same training contract with saved state.
These are different operations.

If an independent test result guides changes, retire that scored test into
development. Create and freeze a fresh independent test before the next release
decision. Do not reuse the old test as independent evidence. A training-only
change based solely on development leaves untouched sealed sets eligible.

## 14. Finish the release package and documentation

`scripts/package_weights.py` currently creates a checksummed candidate package
and basic README. It does not create a complete model card, training-lineage
dossier, or automatic final readiness decision. Those are still required work.
No promised lineage-packaging code was added before this pause.

The final package must include:

- Selected adapter, exact base revision and hash, complete tokenizer, formatter,
  tool contract, greedy settings, and file checksums.
- Minimal working inference example with expected result and clear proposal-only
  behavior. Instructions must work without LeanRouter or hidden local paths.
- Direct dependency pins, the tested torch installation command, and a full
  tested environment lock or freeze with platform/Python notes.
- A model card describing supported tasks, languages, input limits, base/LoRA
  details, training phases, chosen checkpoint, authored-data provenance,
  redistribution basis, and limitations.
- Complete development, context, independent challenge, and sealed evaluation
  results, denominators, uncertainty, raw rejection behavior, and known failures.
- Measured startup, full-output latency, process RAM, CUDA allocation/reservation,
  hardware, precision, and whether other GPU jobs were active.
- Training lineage through V2 selected step 400, V3 selected step 200, original
  V4, paused step 300, and resumed V4. Include source/data/adapter hashes and
  distinguish copied checkpoints from resumed training output.
- License and attribution files. The pinned Qwen upstream license is Apache-2.0;
  `LICENSE-QWEN` and `NOTICE` are already staged by the packager. Verify the final
  adapter/runtime distribution terms and authored-data provenance before release.

Upstream license evidence: [pinned Qwen license](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/7ae557604adf67be50417f59c2c2f167def9a775/LICENSE).
The saved license hash is
`832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e`.
The upstream inventory had no separate NOTICE file. Existing candidate packaging
does not by itself finish the release-license review.

Keep package contents immutable during scored inference. After final documentation
changes, regenerate the checksum manifest deliberately, preserve the evaluated
adapter/runtime hashes, and repeat clean loading on the final artifact. Any
weight merge, quantization, tokenizer, prompt, or inference-code change requires
applicable quality evaluation of that changed artifact, not just a smoke test.
There is no existing finalization script that performs these steps automatically.

Update `goal.md` and [MODEL_RELEASE_PROGRESS.md](MODEL_RELEASE_PROGRESS.md) only
with verified receipts. State training completion separately from weight-release
status. Mark `WEIGHTS READY FOR RELEASE` only when all remaining quality,
export, clean-load, packaging, provenance, and licensing requirements are met.
Public upload and production deployment remain separate future actions.

## 15. Files to read in the next session

1. This handoff and `artifacts/model-release/pro-training-v4/pause_receipt.json`.
2. [MODEL_RELEASE_PROTOCOL_V1.md](MODEL_RELEASE_PROTOCOL_V1.md) for fixed gates.
3. [MODEL_RELEASE_TRAINING_V4.md](MODEL_RELEASE_TRAINING_V4.md) for the current budget.
4. [MODEL_RELEASE_PROGRESS.md](MODEL_RELEASE_PROGRESS.md) and selection receipts
   for historical evidence and failed candidates.
5. `scripts/pilot_train.py`, `wrench/sft.py`, `scripts/release_eval.py`,
   `scripts/release_select.py`, `scripts/package_weights.py`, and
   `scripts/verify_weight_package.py` before changing their contracts.

Preserve unrelated dirty work and sibling repositories. No commit, push,
publication, deployment, new training run, or further model evaluation is part
of preparing this handoff.
