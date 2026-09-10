# Repository organization and clone audit

Completed September 10, 2026.

## Layout

- data/releases holds frozen V21, V20 and context-release-v2b inputs.
- data/archive/baseline retains the previous baseline for historical reference and existing tests.
- artifacts/archive preserves prior experiments, raw acquisitions, unpromoted builds, and sidecar state.
- releases/v21 exposes release cards, evidence, checksums and a versioned remote asset catalog.
- requirements provides training and test dependencies.
- scripts/README.md identifies maintained entry points and historical tools.
- examples/legacy-sidecar isolates the older container example.

All 222 pre-cleanup data files were accounted for after relocation. Only data/README.md and the historical baseline train.jsonl changed bytes. The latter had three credential-shaped occurrences redacted; its redaction.json records original and sanitized hashes. Original material remains in the local pre-cleanup snapshot, not the distributed source bundle.

## Distributed assets

Five private, checksummed Hugging Face bundles preserve the full frozen V21 package, V20 initializer, authored dataset history, training evidence/source receipts, and original source/documentation. The asset catalog pins revision 466e6f269f16179ce87b47180f5624b178cbe11b. All five remote LFS SHA-256 values matched the catalog.

Raw acquisitions and gateway traces remain local. They are not V21 authored training inputs and are not claimed as redistributable release data. The original-source bundle excludes historical datasets, which are separately catalogued. Intermediate optimizer snapshots remain local under the model storage policy.

## Portability repairs

Training can explicitly download the pinned base with --download-base. Documentation also supplies an explicit cache population command for offline preflight/evaluation. Current generators accept new output locations under artifacts. Historical script defaults no longer reference the author's checkout, and legacy mutation workflows use scratch data.

The downloaded package initially failed after relocation because normal imports rewrote checksummed Python bytecode. Package verification now launches Python with -B, packaged evaluation disables bytecode writes, and the quickstart documents -B. Frozen package files and hashes were not changed.

## Validation

- Full test suite: 158 passed, one PEFT warning.
- Clean index export: 158 passed using the installed CPU Python environment. This was a clean file export, not a freshly provisioned dependency environment.
- Release file catalog: 49 files verified.
- Both maintained generators reproduced the frozen dataset JSONL hashes.
- V21 training semantics: zero errors and warnings.
- Token/data preflight: passed using the populated local tokenizer cache.
- Clean-export download restored 56 package files.
- Relocated downloaded package: passed original manifest checks and two expected CUDA predictions using the existing release Python environment, an explicit pinned base, and an empty model cache.
- Follow-up verifier/downloader tests after the bytecode fix: 8 passed.
- Fresh Ubuntu/Python 3.11 GitHub runner installed dependencies, verified all 49 release files, and passed 158 tests (one warning). [CI run 34500892770](https://github.com/stancsz/wrench-slm/actions/runs/34500892770) tested commit 759c0ef.

No new training run or router deployment was performed. The adapter weights and package manifest retain their original hashes.
