# Phase 370: 5060 Ti Drive Queue Dispatch

Date: 2026-09-21

Status: `PENDING_WORKER_CLAIM`

## Purpose

Use the repository's prescribed private Google Drive queue after the Codex
remote execution channel returned empty turns. The job is nonce-bound and
targets the current source commit and pinned Hugging Face revision.

## Dispatch receipt

- Queue folder: `jobs/pending`
- Queue folder id: `16Cyxb70EcN5hBhDaEjNdDaKmi44d4Wvv`
- Drive file: `wrench-5060ti-current-package-20260921-03.json`
- Drive file id: `1vCabBoPaTzrcpe09l87-YR-vpcaYaubD`
- Target host: `DESKTOP-KET1SKP`
- Required GPU: `NVIDIA GeForce RTX 5060 Ti`
- Job id: `wrench-5060ti-current-package-20260921-03`
- Claim nonce: `0ecdb8ff90ee482f898a8339ee8548d9`
- Source commit: `cb7fd30b85a791ba5bec0f0e4b5f8aaf8d64b9d1`
- Hugging Face revision: `9c6303c2c17a3798a134388c7e544728b22bd481`
- Manifest SHA-256: `9d91e147e5c68a95a74200949aa0e31dc284bd86465de71be298cb1276a525bb`

## Observation

The Drive listing was read back immediately after upload and again after a
30-second observation window. The manifest remained in `jobs/pending`; the
target job did not appear in `jobs/running`, `jobs/completed`, or `jobs/failed`.
This proves queue upload and readback only. It does not prove worker claim,
execution, GPU identity, package validation, or benchmark success.

## Acceptance boundary

Promote a 5060 Ti result only after a completed or failed worker receipt echoes
the job id and nonce and reports the target host, GPU, exact pins, resource
snapshots, bounded command, exit code, and receipt hashes. Until then the
independent hardware gate remains open.
