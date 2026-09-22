# Phase 372: 5060 Ti Current-HEAD Queue Dispatch

Date: 2026-09-21

Status: `PENDING_WORKER_CLAIM`

The earlier queue manifest was pinned before the latest evidence commits. A
new manifest was generated from the current repository HEAD and uploaded to
the prescribed private Drive `jobs/pending` folder. The older manifest was not
deleted or modified.

## Current job

- Drive file: `wrench-5060ti-current-package-20260921-04.json`
- Drive file id: `1tXiJce_L1FkVgRqakCPhnG6USVmgjEBQ`
- Job id: `wrench-5060ti-current-package-20260921-04`
- Claim nonce: `7dab95c411cf4039b23a5e2633e9f875`
- Source commit: `8391b72da22915a0b9c8fa277446541efecd7412`
- Hugging Face revision: `9c6303c2c17a3798a134388c7e544728b22bd481`
- Manifest SHA-256: `b3cb3dca5df98f80ebf1b571dbff95505a38ce4221c35c49d1b3d0f18f0296c6`
- Target: `DESKTOP-KET1SKP`, NVIDIA GeForce RTX 5060 Ti

The upload was read back from the pending folder. No execution, GPU
attestation, resource snapshot, package validation, or benchmark result is
claimed until the worker moves this exact manifest to a terminal queue state
and returns a nonce-bound receipt.
