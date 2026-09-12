# Pro training V7 contrast budget

Prepared 2026-09-10 after V6 passed the fixed 176-case development suite and
the 37-case packaged context guard, but failed fresh external evaluation. This
phase is a bounded correction for semantic tool selection and exact protocol
handling. It is the last planned correction in this handoff before a release
decision is reconsidered from fresh external evidence.

## Evidence that requires V7

The selected V6 step-300 adapter has SHA-256
`819573bd191b766d2f67f71a09055eb9b349a0ca6ae58f2dce13d6264e9c4a9e`.
All V6 checkpoints at steps 100, 200, and 300 scored 176/176 on the unchanged
development set, with every fixed gate passing. The exact step-300 package
scored 37/37 on the fresh context-development-v2 guard, and the clean offline
CUDA verifier passed with the pinned base and fresh Python environment.

The fresh independent challenge-v2 then scored 57/66 exact (86.36%), with
routine exact 35/42 (83.33%). The fresh sealed release-authoring-v2 set scored
396/440 exact (90.00%), with routine exact and actual outcomes 236/280
(84.29%). Raw protocol validity was 100% on the sealed set but only 96.97% on
the challenge. The release thresholds therefore failed.

The failures are concentrated rather than a general fixture problem:

- configuration requests sometimes become `git status --short`;
- Git-status requests sometimes become `read_file` on a distractor path;
- one Git-log request became a search call;
- one search request became a file read;
- some draft calls lose the final newline in the body;
- one invalid range produced a `read_file` call instead of fallback;
- one unavailable-tool request produced a malformed output;
- a few Chinese requests abstain when a direct call is expected.

The V6 challenge and sealed results are now retired as independent evidence
because they informed V7. They remain preserved diagnostic receipts. A fresh
challenge-v3 and fresh sealed release set-v3 must be authored after V7 before
any final release claim.

## Data contract

The V7 training directory is `data/pilots/release-generalization-v7`.

- Training rows: 25,930
- Training families: 168
- Training SHA-256: `c39cff1c0687e6e2b1aa176894fb035816ac754cde9337510d9e787cf15dab8d`
- Parent V6 train SHA-256: `688af1e8f381fdab3ea5d7283b3d34d7c6d146e3499355ed67d2bfa5c6ce072d`
- Generator SHA-256: `b6c0dcdd98988ff7ffcc00f03685ca0e3c1e4f813c77f51c85fce9255bcf450c`
- Development: the unchanged 176-row fixed development file
- Evaluation: the unchanged 440-row V4 release evaluation file
- Dropped duplicates: zero
- Label conflicts: zero
- Cross-split exact inputs and families: zero

The additions are fresh authored contrast families. They state the semantic
boundary directly in varied English and Chinese wording: configuration reads
versus Git status, Git log versus file/search tools, literal search versus
other inspection tools, and file reads versus drafts. They include explicit
terminal-newline preservation for drafts and explicit fallback requirements for
invalid ranges and unavailable tools. No row from challenge-v2, sealed-v2,
context-development-v2, or any scored prediction output was imported.

The preflight receipt is
`artifacts/model-release/data-preflight-v7/preflight.json`. It passed with the
same maximum training length of 604 tokens, maximum prompt length of 554
tokens, and maximum completion length of 53 tokens. The base revision,
formatter, tokenizer, and package versions match the frozen protocol.

## Initializer and training budget

Initialize from the selected V6 step-300 adapter at
`artifacts/model-release/pro-training-v6/checkpoint`. Verify its SHA-256 before
launching:

`819573bd191b766d2f67f71a09055eb9b349a0ca6ae58f2dce13d6264e9c4a9e`

Reset the optimizer and do not pass `--resume-from`. V7 is a new data phase;
the V6 optimizer state must not be reused. First run a one-step warm-start
diagnostic with at most 16 presentations. It proves the initializer, formatter,
tokenizer, and optimizer reset, but is not a candidate.

The main run is bounded to 300 optimizer steps, with checkpoints at steps 100,
200, and 300. This is at most 4,800 example presentations and 60 minutes of
wall time including validation and checkpoint writes. Use:

- base `Qwen/Qwen2.5-0.5B-Instruct` at revision
  `7ae557604adf67be50417f59c2c2f167def9a775`;
- LoRA rank 16, alpha 32, dropout 0.05 on q/k/v/o and gate/up/down;
- microbatch 2, accumulation 8, effective batch 16;
- constant learning rate `0.00001`, seed 42, BF16;
- maximum sequence length 1536 and CUDA allocator fraction 0.55.

The receipt is valid only when it reports completion, 300 steps, 4,800
presentations, finite losses, all checkpoints, V7 train and validation hashes,
the expected V6 initializer hash, and `optimizer_reset: true`. Preserve any
failed run in place and use a new output directory for a rerun.

## Commands

Run from the repository root after confirming no competing GPU process:

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v7/train.jsonl `
  --val data/pilots/release-generalization-v7/development.jsonl `
  --output artifacts/model-release/warmstart-diagnostic-v7 `
  --steps 1 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.00001 --seed 42 --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v6/checkpoint

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v7/train.jsonl `
  --val data/pilots/release-generalization-v7/development.jsonl `
  --output artifacts/model-release/pro-training-v7 `
  --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.00001 --seed 42 --checkpoint-every 100 `
  --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v6/checkpoint
```

Require the diagnostic receipt to pass before starting the main run. Do not
select a checkpoint from the diagnostic.

## Development selection and package checks

Evaluate all V7 checkpoints on the unchanged 176-case development file with
real disposable fixtures:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v7 --checkpoint artifacts/model-release/pro-training-v7/step-000100 --output artifacts/model-release/v7-development-step100 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v7 --checkpoint artifacts/model-release/pro-training-v7/step-000200 --output artifacts/model-release/v7-development-step200 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v7 --checkpoint artifacts/model-release/pro-training-v7/checkpoint --output artifacts/model-release/v7-development-step300 --execute

.venv\Scripts\python.exe -X utf8 scripts/release_select.py `
  --training-run artifacts/model-release/pro-training-v7 `
  --evaluations artifacts/model-release/v7-development-step100 artifacts/model-release/v7-development-step200 artifacts/model-release/v7-development-step300 `
  --output artifacts/model-release/selection-v7
```

Selection remains highest exact rate, then lowest validation loss, then
earliest step. Every fixed gate must pass. Do not select by challenge-v2 or
sealed-v2 scores, and do not lower a threshold after seeing V7 output.

Package only the selected checkpoint:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/package_weights.py `
  --checkpoint <selected-checkpoint-from-selection-v7> `
  --output artifacts/model-release/package-selected-v7 `
  --license artifacts/model-release/licensing-v1/LICENSE-QWEN
```

Run `context-development-v2` through the exact package as a development guard,
then repeat the clean offline CUDA verifier. The guard target remains at least
35/37 exact predictions and outcomes, with the quickstart passing. If another
context guard becomes evidence for another training correction, retire it and
author a new guard version.

## Fresh release evidence after V7

Create fresh challenge-v3 and sealed release-authoring-v3 only after V7 is
selected. Both must have new paths, markers, URLs, entities, prompt wording,
tool ordering, distractors, and language variants. Do not copy V2 rows and
change only identifiers. Freeze each manifest and generator hash before
running the package. Run gold fixture checks without model invocation and keep
the resulting receipts.

Score the exact packaged V7 artifact. Record the package manifest hash, adapter
hash, pinned base checksum, data manifest hashes, generator hashes, frozen
thresholds, and all denominators before scoring. Report raw protocol validity,
exact calls, actual outcomes, explicit fallback, per-kind slices, language
slices, family uncertainty, and filesystem changes. A valid call with the wrong
tool or wrong complete arguments remains a failure.

V7 is release-ready only if the fixed development gates, context guard, clean
package verifier, fresh challenge, and fresh sealed set all pass. Otherwise
label it `TRAINED CANDIDATE`, preserve the receipts, and identify the blocker.
Any test set used to justify another training change is retired before that
change and cannot be reused as final independent evidence.

## Scope and stop rule

This is a model-weight phase. Router behavior, Cloudflare integration, cloud
comparison, hosted-service soak, and public upload remain separate. If V7
passes the fresh external sets, finish the model card, data and licensing
review, dependency freeze, resource report, checksums, and minimal inference
instructions. If V7 fails, do not start an unlimited sequence of corrections;
write a new evidence-based budget with a clear target and preserve V7 as the
latest candidate.
