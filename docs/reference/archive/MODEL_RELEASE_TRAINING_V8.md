# Pro training V8 semantic disambiguation budget

Prepared 2026-09-10 after V7 improved the fresh independent challenge but did
not pass the fresh sealed set. This is a final bounded correction for the
remaining ordinary-wording failure mode. It keeps the release protocol and
thresholds fixed. It does not authorize lowering a gate or reusing a scored
set as final evidence.

## V7 evidence

The V7 step-300 adapter, SHA-256
`fea4719f247812df76d67186930cc03630fb2bb061e51a41526d12e12297cdee`, passed
all 176 unchanged development cases and the 37-case packaged context guard.
The clean offline CUDA verifier passed with the pinned Qwen base.

On fresh challenge-v3, V7 scored 62/66 exact, raw protocol validity 66/66,
routine exact 39/42, and routine actual outcomes 39/42. This was a meaningful
improvement over V6, but it missed the 95% routine floor and per-kind floor.
On fresh sealed-v3, V7 scored 385/440 exact and 225/280 routine exact and
outcomes. Configuration scored 25/40, Git status 20/40, and Git log 20/40.
The other kinds passed. Every sealed failure came from the ordinary release
wording families with two resource distractors, all three tools listed, and no
prior selection result. The model often chose `read_file` for Git status or
Git log and `git status --short` for a configuration region request.

Challenge-v3 and sealed-v3 are retired as independent evidence because their
findings define V8. Preserve their manifests and score receipts. After V8,
author fresh challenge-v4 and sealed-v4 before making the final release
decision.

## V8 data

The training directory is `data/pilots/release-generalization-v8`.

- Training rows: 30,026
- Training families: 200
- Training SHA-256: `0e48f61a131ba2247605ebe0e0440155a22f36a9db92f7ac9fde9ad0930308bd`
- Parent V7 train SHA-256: `c39cff1c0687e6e2b1aa176894fb035816ac754cde9337510d9e787cf15dab8d`
- Generator SHA-256: `7154e68d066272986dc443edb0bb4cfc3b1698837533fbcaaa25a776d070b499`
- New rows: 4,096 semantic disambiguation examples
- Development: unchanged 176-row fixed development file
- Evaluation: unchanged 440-row release file used only for development tooling
- Dropped duplicates: zero
- Label conflicts: zero
- Cross-split exact inputs and families: zero

V8 adds eight fresh wording families per affected kind. Four are English and
four Chinese. Configuration, Git status, and Git log rows use a normalized
context with two resource distractors, all tools present, and no prior result,
matching the observed sealed failure context. Configuration wording teaches
that a region request requires `read_file`; Git status and Git log wording
teaches the corresponding `exec_command` operation. Missing-tool examples
teach explicit fallback when `read_file` is absent. No scored prompt, output,
fixture, or prediction is imported.

The preflight receipt is
`artifacts/model-release/data-preflight-v8/preflight.json`. It passed with
maximum full training length 604 tokens, maximum prompt 554 tokens, and
maximum completion 53 tokens. The base revision, formatter, tokenizer, and
package versions are unchanged.

## Initializer and bounded budget

Initialize from the selected V7 step-300 adapter at
`artifacts/model-release/pro-training-v7/checkpoint`. Verify the initializer
SHA-256 before launch:

`fea4719f247812df76d67186930cc03630fb2bb061e51a41526d12e12297cdee`

Reset the optimizer and do not pass `--resume-from`. Run a one-step diagnostic
with at most 16 presentations first. It must report the expected initializer,
formatter and tokenizer, `optimizer_reset: true`, and a completed checkpoint.

The main run is limited to 300 optimizer steps, checkpoints at 100, 200, and
300, and 4,800 example presentations. Use a lower learning rate of `0.000005`
to reduce the chance of degrading the already passing draft, search, line,
health, unsupported, invalid-range, and ambiguity behavior. The remaining
settings are fixed:

- base `Qwen/Qwen2.5-0.5B-Instruct` revision
  `7ae557604adf67be50417f59c2c2f167def9a775`;
- LoRA rank 16, alpha 32, dropout 0.05 on q/k/v/o and gate/up/down;
- microbatch 2, accumulation 8, effective batch 16;
- seed 42, BF16, maximum sequence length 1536;
- CUDA allocator fraction 0.55;
- maximum 60 minutes including validation and checkpoint writes.

The main receipt must report completion, 300 steps, 4,800 presentations, finite
losses, all checkpoints, V8 hashes, the expected initializer hash, and a reset
optimizer. Preserve failures and use a new run directory for any rerun.

## Commands

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v8/train.jsonl `
  --val data/pilots/release-generalization-v8/development.jsonl `
  --output artifacts/model-release/warmstart-diagnostic-v8 `
  --steps 1 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.000005 --seed 42 --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v7/checkpoint

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v8/train.jsonl `
  --val data/pilots/release-generalization-v8/development.jsonl `
  --output artifacts/model-release/pro-training-v8 `
  --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.000005 --seed 42 --checkpoint-every 100 `
  --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v7/checkpoint
```

## Selection and package gates

Evaluate V8 steps 100, 200, and 300 on the unchanged development set with
real disposable fixtures:

```powershell
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v8 --checkpoint artifacts/model-release/pro-training-v8/step-000100 --output artifacts/model-release/v8-development-step100 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v8 --checkpoint artifacts/model-release/pro-training-v8/step-000200 --output artifacts/model-release/v8-development-step200 --execute
.venv\Scripts\python.exe -X utf8 scripts/release_eval.py --data data/pilots/release-generalization-v8 --checkpoint artifacts/model-release/pro-training-v8/checkpoint --output artifacts/model-release/v8-development-step300 --execute

.venv\Scripts\python.exe -X utf8 scripts/release_select.py `
  --training-run artifacts/model-release/pro-training-v8 `
  --evaluations artifacts/model-release/v8-development-step100 artifacts/model-release/v8-development-step200 artifacts/model-release/v8-development-step300 `
  --output artifacts/model-release/selection-v8
```

Select only by fixed development exact rate, then validation loss, then
earliest step. A checkpoint with a failed fixed gate is ineligible. Package the
selected checkpoint as an adapter with the pinned base, tokenizer, prompt
contract, license, and checksums. Run the 37-case context guard and the clean
offline CUDA verifier on the exact package. A pass on either guard does not
replace fresh external evidence.

## Fresh final evidence

If V8 passes development, context, and packaging gates, author challenge-v4 and
sealed release-authoring-v4. Use new values, paths, URLs, tool ordering,
contexts, prompt wording, and language variants. Do not copy V3 JSONL or alter
identifiers. Run gold checks without model invocation, freeze each manifest,
and record generator hashes before scoring.

Score only the exact V8 package. Retain raw predictions, parsed actions,
rejections, fallbacks, actual fixture outcomes, per-kind and language slices,
family uncertainty, filesystem-change checks, package and base hashes, and
clean-environment receipts. Apply every frozen protocol threshold. If V8
findings are used for another training phase, retire V4 and author V5 before
that phase.

The final status can be `WEIGHTS READY FOR RELEASE` only if the fixed
development gates, context guard, clean package verifier, fresh challenge-v4,
fresh sealed-v4, model card, licensing review, dependency freeze, checksums,
resource report, and inference instructions all pass. Otherwise retain
`TRAINED CANDIDATE` and state the exact blocker. Router and hosted-service work
remain outside this weight-release decision.
