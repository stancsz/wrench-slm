# Pro training V6 generalization budget

Prepared 2026-09-09 after V5 passed the fixed development gates and the fresh
context guard, but failed newly scored held-out checks. This is a bounded
generalization phase. It addresses observed confusion between semantically
similar tool requests while preserving the pinned model, prompt formatter,
inference contract, and fixed development protocol.

## Why V6 exists

The V5 candidate was trained from the verified V4 step-450 adapter and passed
all 176 unchanged development cases at every scored checkpoint. The selected
step-300 package also passed the fresh 37-case context-development guard at
37/37 exact predictions and 37/37 actual outcomes. The clean CUDA verifier
loaded the exact package in a fresh Python 3.14 environment and completed two
offline quickstart calls.

Those results establish a strong trained candidate, but they do not establish
release readiness. The first held-out independent challenge scored 55/66 exact
(83.33%), and the held-out sealed set scored 399/440 exact (90.68%). The raw
protocol itself was valid, but the fixed quality gates failed. The largest
systematic issue was semantic tool confusion: configuration requests often
produced `git status`, while Git status requests often produced a file read.
Other failures included malformed search text, the wrong tool for Git log, a
missing trailing newline in a draft, and incorrect handling of a missing tool.

The challenge and sealed results are useful diagnosis. They are no longer
eligible as independent release evidence after influencing this training
phase. A new challenge and a new sealed release set must be authored after V6
and scored only on the exact final package. The original 176-case development
set remains the fixed selection gate. The V5 context guard remains a
development guard; it is not a final release test.

## V6 data

The training directory is `data/pilots/release-generalization-v6`.

- Version: `release-generalization-v6`
- Training rows: 22,858
- Training families: 136
- Training SHA-256: `688af1e8f381fdab3ea5d7283b3d34d7c6d146e3499355ed67d2bfa5c6ce072d`
- Parent V5 training SHA-256: `be83cbfb2547488dc04351f0bcf446f3715322d6d2389d6ae8beff9f828d2606`
- Generator SHA-256: `4238fbb78236fa435156a7830757e56e6d40978ee6f7607d0cab3678af283da4`
- Development: the unchanged 176-row V5 development file
- Evaluation: the unchanged 440-row V4 release evaluation file
- Cross-split exact inputs: zero
- Cross-split family overlap: zero

The V6 additions are fresh authored semantic wording families. They cover
configuration inspection, line extraction, search, Git status, Git log, health
checks, draft creation, missing-tool handling, and invalid ranges. They vary
the wording and tool context without importing rows from the scored challenge,
the scored sealed set, or either context guard. The data generator records
zero dropped duplicates and zero label conflicts.

The V6 preflight receipt is
`artifacts/model-release/data-preflight-v6/preflight.json`. It passed with a
maximum training length of 604 tokens, a maximum prompt length of 554 tokens,
and a maximum completion length of 53 tokens. The declared base revision,
formatter hash, tokenizer, and package versions match the existing training
contract.

## Initializer and optimizer policy

Initialize from the selected V5 step-300 adapter at
`artifacts/model-release/pro-training-v5/checkpoint`. The expected adapter
SHA-256 is
`378612c58bef39cc870854683e857150eed692120abdb692eb66c614c29a532d`.

This is a warm start with a new optimizer state. Do not use `--resume-from`.
The V5 optimizer history belongs to a different data distribution and must not
control V6 updates. The warm-start diagnostic must prove that the initializer
loads and the optimizer is reset before the main run begins.

The diagnostic is limited to one optimizer step and 16 example presentations.
Its output is not a candidate and must not be used for selection. The main run
uses the same adapter configuration as V5:

- Base: `Qwen/Qwen2.5-0.5B-Instruct`, revision
  `7ae557604adf67be50417f59c2c2f167def9a775`
- LoRA: rank 16, alpha 32, dropout 0.05
- Target modules: q, k, v, o, gate, up, and down projections
- Trainable parameters: 8,798,208
- Formatter SHA-256: `3c3d37ec3481da3bedc4f4148c20699c55b3358566e2f253a4caac7b2c4e3ade`
- Microbatch: 2
- Gradient accumulation: 8
- Effective batch: 16
- Learning rate: `0.00001`
- Seed: 42
- Precision: BF16
- Maximum sequence length: 1536
- CUDA allocator fraction: 0.55

## Bounded compute and stopping rules

The main V6 budget is 300 optimizer steps, with checkpoints at steps 100, 200,
and 300. This is at most 4,800 example presentations. The run must finish
within 60 minutes including validation and checkpoint writes. Do not extend the
step count because training loss continues to fall, and do not retry a failed
run into the same output directory. Preserve a failed receipt and use a new
versioned run directory if a rerun is justified.

The run is valid only if its receipt reports `status: completed`, exactly 300
steps, 4,800 presentations, finite losses, all three checkpoints, the V6 train
and validation hashes, the expected base revision, and the expected
initializer adapter hash. Record peak PyTorch allocation and the process exit
code. A lower validation loss or a successful process exit without output
quality evidence does not approve the weights.

## Commands

Run from the repository root after confirming that no other process is using
the GPU:

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v6/train.jsonl `
  --val data/pilots/release-generalization-v6/development.jsonl `
  --output artifacts/model-release/warmstart-diagnostic-v6 `
  --steps 1 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.00001 --seed 42 --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v5/checkpoint

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v6/train.jsonl `
  --val data/pilots/release-generalization-v6/development.jsonl `
  --output artifacts/model-release/pro-training-v6 `
  --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.00001 --seed 42 --checkpoint-every 100 `
  --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v5/checkpoint
```

Before the main command, inspect the diagnostic receipt and require all of the
following: the V5 adapter hash matches, the base revision is pinned, the
formatter and tokenizer hashes match, `optimizer_reset` is true, the process
completed, and the output contains a valid checkpoint. If any item fails,
stop and diagnose the initializer or environment before spending the main
budget.

## Checkpoint selection

Evaluate steps 100, 200, and 300 on the unchanged 176-case development set
with real disposable fixtures:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v6 --checkpoint artifacts/model-release/pro-training-v6/step-000100 --output artifacts/model-release/v6-development-step100 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v6 --checkpoint artifacts/model-release/pro-training-v6/step-000200 --output artifacts/model-release/v6-development-step200 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v6 --checkpoint artifacts/model-release/pro-training-v6/checkpoint --output artifacts/model-release/v6-development-step300 --execute

.venv\Scripts\python.exe -X utf8 scripts/release_select.py `
  --training-run artifacts/model-release/pro-training-v6 `
  --evaluations artifacts/model-release/v6-development-step100 artifacts/model-release/v6-development-step200 artifacts/model-release/v6-development-step300 `
  --output artifacts/model-release/selection-v6
```

Selection is based only on the fixed development protocol: highest exact
prediction rate, then lowest validation loss, then earliest step. A checkpoint
is ineligible if any fixed gate fails, even when its aggregate exact count is
higher. The retired challenge, retired sealed set, and context scores must not
be used to choose among V6 checkpoints.

## Package and development guards

Package only the selected V6 checkpoint. The package must retain the exact
base dependency, tokenizer, chat template, adapter configuration, prompt
formatter, licensing file, and checksums:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/package_weights.py `
  --checkpoint <selected-checkpoint-from-selection-v6> `
  --output artifacts/model-release/package-selected-v6 `
  --license artifacts/model-release/licensing-v1/LICENSE-QWEN
```

Run the fresh packaged context guard and keep every raw case output:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py `
  --data data/pilots/context-development-v2 `
  --package artifacts/model-release/package-selected-v6 `
  --base-path artifacts/model-release/base-dependency-v1 `
  --output artifacts/model-release/v6-package-context-development --execute
```

The guard target is at least 35/37 exact predictions and 35/37 actual
outcomes, with the packaged quickstart passing. Keep all 37 cases in the
denominator. If V6 scores below that target, classify each failure as a model,
label, fixture, or packaging problem. Do not lower the guard, discard difficult
cases, or count fallback conversion as a correct model prediction.

Run the clean CUDA verifier on the exact package after the development gates
pass. Record the package manifest hash, adapter hash, base checksum, peak CUDA
allocation and reservation, process-tree RSS, load time, first-call latency,
warm-call latency, and offline status. These measurements describe the
standalone adapter package; they do not prove router or hosted-service
performance.

## Fresh external evaluation required after V6

Because V5 findings guided this run, create new external sets after the V6
candidate is selected. Do not score the retired 66-case challenge or retired
440-case sealed set as the final evidence.

The fresh independent challenge must be authored by a separate generator and
must use new paths, entities, markers, URLs, prompt wording, tool-order
variations, minimal contexts, and language variants. It must preserve the
existing case schema, include positive tasks and abstention cases, execute
positive actions in disposable fixtures, and be frozen before model scoring.

The fresh sealed release set must likewise use new task families and new
values. It must be generated independently from the training additions, pass
the gold-label and fixture checks, and be frozen with a manifest hash before
the package is evaluated. Keep the authoring source and the scored JSONL under
versioned directories. Do not copy V5 evaluation rows and change only their
wording.

Before scoring either set, record:

1. the package manifest SHA-256 and adapter SHA-256;
2. the base dependency checksum and clean-environment receipt;
3. the data manifest SHA-256, generator hash, family counts, and denominators;
4. the fixed thresholds and scoring version;
5. the fact that the sets were frozen before model outputs were generated.

Score raw protocol validity, exact tool and arguments, actual fixture outcome,
fallback, abstention, language, and task family separately. Keep all cases in
the denominator and publish per-kind failure counts. A valid serialized call
with the wrong tool or wrong argument is a model failure even if a fallback
would make the request appear usable.

## Decision rules

V6 can produce a release candidate only when all of these conditions hold:

- a completed 300-step receipt and recoverable checkpoints are present;
- the selected checkpoint passes every fixed 176-case development gate;
- the exact package passes the fresh context guard and clean CUDA verifier;
- the fresh independent challenge meets the frozen independent thresholds;
- the fresh sealed release set meets the frozen release thresholds;
- raw outputs, actual outcomes, abstentions, language coverage, and failure
  counts are retained;
- model card, lineage, data provenance, license review, dependency freeze,
  resource measurements, and inference instructions are complete.

If the original development set passes but either fresh external set fails,
label the result `TRAINED CANDIDATE`. Preserve all receipts and write a new
bounded budget before another training phase. Any external set whose findings
guide another phase is retired and replaced with a new set before the next
release decision. Never claim `WEIGHTS READY FOR RELEASE` from development or
context scores alone.

If V6 improves held-out generalization but regresses a fixed development gate,
do not release it and do not select it by aggregate score. Investigate the
labels, data balance, or learning budget and keep the V5 package available as
the previous candidate. If the training process fails, preserve the partial
run, identify whether the failure is environmental or methodological, and use
a new run directory for any authorized rerun.

## Required follow-up artifacts

After the V6 decision, update the progress receipt and `goal.md` with the
authoritative hashes and scores. Add or update:

- a V6 training receipt and selection record;
- the exact package manifest and final checksums;
- fresh independent and sealed evaluation manifests and score receipts;
- a model card describing scope, supported tools, limitations, data, and
  licensing;
- a clean-environment inference report with measured resource requirements;
- a release decision that says `NOT READY`, `TRAINED CANDIDATE`, or
  `WEIGHTS READY FOR RELEASE` and names every remaining blocker.

Router integration, cloud routing, hosted service deployment, and public upload
remain separate work. This V6 budget concerns the model weights and their
standalone release evidence only.
