# Pro training V9 long variant

Prepared 2026-09-10 after the 150-step V9 abstention repair failed to restore
the fixed ambiguity gate. This is a separate bounded run, not an automatic
resume. It uses the same V9 data and V8 initializer with enough steps to test
whether the explicit abstention examples were simply under-trained.

The V8 step-300 candidate scored 15/16 on the unchanged ambiguous slice. The
150-step V9 variant scored 8/16 and was ineligible despite perfect routine
behavior. No external V4 set is being scored until a checkpoint passes every
fixed development gate.

## Contract

- Data: `data/pilots/release-generalization-v9/train.jsonl`
- Train SHA-256: `bbc79b84a734495abdda5d0ade0ba59ae3aff59046465569c4b6d17535f7ee0e`
- Initializer: `artifacts/model-release/pro-training-v8/checkpoint`
- Initializer adapter SHA-256: `89305a1b591142076ec221bee5e6a8c19bfdb1f79d6e1c2b13d8faa9e9320c43`
- Optimizer: fresh, with no `--resume-from`
- Steps: 300, checkpoints at 100, 200, and 300
- Presentations: at most 4,800
- Learning rate: `0.000005`
- Microbatch 2, accumulation 8, BF16, maximum length 1536, seed 42
- CUDA allocator fraction: 0.55

Use a new output directory. The run is valid only with a completed receipt,
finite losses, all checkpoints, the V9 hashes, and the expected initializer
hash. Evaluate every checkpoint on the unchanged 176-case development set.
Select only a checkpoint with every fixed gate passing. If all three fail the
ambiguity gate, retain V8 and stop this correction line.

```powershell
Set-Location 'C:\Users\stanc\github\portfolio\wrench-slm'

.venv\Scripts\python.exe -X utf8 scripts/pilot_train.py `
  --train data/pilots/release-generalization-v9/train.jsonl `
  --val data/pilots/release-generalization-v9/development.jsonl `
  --output artifacts/model-release/pro-training-v9-long `
  --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 `
  --learning-rate 0.000005 --seed 42 --checkpoint-every 100 `
  --gpu-memory-fraction 0.55 `
  --initialize-adapter artifacts/model-release/pro-training-v8/checkpoint
```

If a checkpoint passes, package the exact selected adapter, rerun the context
guard and clean CUDA verifier, then author fresh challenge-v4 and sealed-v4.
The retired V3 sets must not be reused. If no checkpoint passes, the weight
status remains `TRAINED CANDIDATE` and no external release claim is made.
