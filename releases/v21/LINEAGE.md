# Wrench-Pro v21 lineage

## Base dependency

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Base weight SHA-256: `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`
- Upstream license SHA-256: `832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e`

## Data and training

- V21 train manifest: `release-generalization-v21`, train SHA-256
  `7734344c4f5097eee9aaf7efaced62727a32545a8103d628af239471026e1c30`.
- Formatter SHA-256: `3c3d37ec3481da3bedc4f4148c20699c55b3358566e2f253a4caac7b2c4e3ade`.
- Initial adapter: V20 package adapter SHA-256
  `a15d22b2f30287a1ccc26100c4e0e552f0516c8d05a8639bbbf07ee3be2e0fda`.
- Training receipt: `pro-training-v21/run.json`, SHA-256
  `22ce0230b4523e6632fcda0a77187797189fa4ad6adad33ce4bfcebe8f3e51df`.
- Selected checkpoint: V21 step 200, selected by the recorded development
  rule.

## Package

- Adapter SHA-256:
  `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`.
- Package manifest is `release_manifest.json`; it covers every distributed file
  except itself.
- The context suite was generated after this adapter was frozen and was never
  imported into training.

The repository retains source snapshots, data manifests, selection receipts,
evaluation summaries, and environment receipts under `artifacts/model-release`.
Optimizer state and historical model weights are not part of this package.
