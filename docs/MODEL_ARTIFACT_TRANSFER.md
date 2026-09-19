# Model artifact transfer and 5060TI synchronization

This repository keeps source code, tests, receipts, and instructions separate from large model artifacts. The current BF16 checkpoint is transferred through a separate private Git LFS repository.

## Private artifact repository

- Repository: https://github.com/stancsz/wrench-slm-artifacts
- Visibility: private
- Verified main commit: `e0ebd6f3762e30a118ade6bc47e01fc65d8e3eea`
- Artifact: `models/Wrench-Qwen3.6-8expert-BF16`
- Contents: 9 safetensor shards plus tokenizer and runtime metadata
- Uploaded size: approximately 7.9 GB
- Local integrity check: `git lfs fsck` passed before handoff
- Manifest: `artifact-manifest.json`

The artifact repository is experimental. Its existence does not authorize learned routing, deployment, provider spending, a live pilot, or a production claim.

## Parameter and size interpretation

These values describe different measurements and must not be substituted for one another:

- The transferred BF16 state-dict element total is `3,945,236,336`; this includes visual tensors in the source artifact.
- The text-only Wrench runtime receipt reports `3,881,244,016` parameters after the visual tensors are excluded.
- The transferred files occupy approximately 7.9 GB on disk.
- The 3.8B to 4.25B parameter budget in `GOAL.md` is a parameter constraint, not a disk-size or VRAM claim.

Always cite the artifact commit and verify every file against `artifact-manifest.json` before loading it.

## Fetch on the 5060TI worker

Keep the artifact outside the source checkout. Do not commit model files into this repository.

```powershell
git lfs install
git clone --depth 1 https://github.com/stancsz/wrench-slm-artifacts.git C:\models\wrench-slm-artifacts
Set-Location C:\models\wrench-slm-artifacts
git lfs pull --include="models/Wrench-Qwen3.6-8expert-BF16/*"
git checkout e0ebd6f3762e30a118ade6bc47e01fc65d8e3eea
```

After the pull, verify the manifest hashes before using the checkpoint. Keep the artifact read-only and cache it locally so repeated jobs do not download the weights again.

## Synchronize source code and instructions

From the source checkout on the 5060TI worker:

```powershell
git fetch origin main
git status --short
git pull --ff-only origin main
```

If the working tree is dirty, do not overwrite local work. Report the changed paths and wait for a safe integration decision.

The worker should read:

- `GOAL.md`
- `AGENTS.local.md`
- `docs/MODEL_ARTIFACT_TRANSFER.md`
- the relevant phase README and receipt files

The worker must report the source commit, artifact commit, artifact hash verification result, runtime identity, GPU memory, wall-clock time, retries, and final job status. A downloaded file alone is not a completed run.

## Execution boundary

Wrench remains proposal-only and fail-closed. Keep learned routing `DISABLE`, preserve the stronger-model fallback, and do not treat a local load or one-request smoke as evidence of production value.
