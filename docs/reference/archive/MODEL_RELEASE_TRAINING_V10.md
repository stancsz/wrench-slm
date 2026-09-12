# Pro training V10 ordinary-wording ambiguity budget

Prepared 2026-09-10 after the V9 short and long variants both returned
175/176 on the fixed development set. The remaining miss is the same ordinary
English ambiguity wording that asks for an appropriate service configuration
without selecting a service. V10 adds a final focused contrast set and uses a
fresh optimizer. It is bounded and will stop if the ambiguity gate does not
recover. The run and all planned V10 checks are complete. For the current
decision and the V11 continuation, use
[MODEL_RELEASE_HANDOFF.md](MODEL_RELEASE_HANDOFF.md).

## Evidence

V8 step 300, V9 step 200, and V9-long step 300 each restore 15/16 ambiguous
development cases while all 112 routine cases and the other fallback slices
pass. The fixed gate requires at least 95% explicit correct ambiguity
abstention, so 15/16 is below the required floor. The V9 additions improved
explicit abstention examples but did not generalize to the ordinary phrase
“appropriate service config.” V10 restored the full 176/176 development score,
but the exact packaged adapter later scored 64/66 on independent challenge v4
and 400/440 on sealed release v4. Both external receipts fail at least one
fixed gate and are recorded under `artifacts/model-release`.

## Data

`data/pilots/release-generalization-v10` contains:

- 33,098 training rows in 216 families;
- train SHA-256 `e81fbf6c4089169582b2c542742caacd2806e5781879d82e16acb0bfda9a066d`;
- parent V9 train SHA-256 `bbc79b84a734495abdda5d0ade0ba59ae3aff59046465569c4b6d17535f7ee0e`;
- generator SHA-256 `a6bc8aecf8e47a81d8a6113c4a54f9d0f30532bdc6f4ad01c7a2055e2d5c5ea4`;
- 2,048 new ordinary-wording ambiguity rows in eight fresh families;
- unchanged development and evaluation files;
- zero dropped duplicates, zero label conflicts, and zero cross-split overlap.

The new rows place two distractor resources in context, leave the prior
selection empty, and distinguish a request for the right config from a request
that identifies a selected service. Four English and four Chinese templates
are repeated across fresh values. Preflight passed with maximum full training
length 604, maximum prompt 554, and maximum completion 53 tokens.

## Bounded run

Initialize from `artifacts/model-release/pro-training-v9-long/checkpoint` with
adapter SHA-256
`bccfe27a02ee680bbc0873fa11b763f64f2c38e3dd733f1aeea98f22961c69b0`. Reset
the optimizer and do not use `--resume-from`. Use 300 steps, checkpoints at
100, 200, and 300, microbatch 2, accumulation 8, learning rate `0.000005`,
seed 42, BF16, maximum length 1536, and CUDA allocator fraction 0.55. The
budget allows at most 4,800 presentations and 60 minutes including validation.

Run the one-step warm-start diagnostic first. The main receipt must report the
V10 train and validation hashes, expected initializer, reset optimizer, finite
losses, and all checkpoints.

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v10/train.jsonl `
  --val data/pilots/release-generalization-v10/development.jsonl `
  --output artifacts/model-release/pro-training-v10 `
  --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.000005 --seed 42 --checkpoint-every 100 `
  --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v9-long/checkpoint
```

V10 checkpoints were evaluated on the unchanged development set. Steps 100,
200, and 300 each scored 176/176; step 300 was selected by the lowest
validation loss. The selected adapter hash is
`9836c73fa802ec2584004814b9061836d392c9220ab55d35821d7a23f4bf4669`.

The selected package passed context-development-v2 at 37/37 and the clean CUDA
verifier. It remains a `TRAINED CANDIDATE` because the fresh external scores
failed the routine and slice gates. Do not rerun V10 or lower the thresholds.
Follow the V11 correction and fresh-v5 evaluation sequence in the canonical
handoff. A release claim still requires all model-quality, packaging,
licensing, model-card, dependency, checksum, and resource gates.
