# Phase 375: Full 5060Ti Verification Workload

Date: 2026-09-21

Status: `IMPLEMENTED_NOT_DISPATCHED_DRIVE_TARGET_UNAVAILABLE`

## Progress

The old 5060Ti job only performed HF package preflight and one mechanical
smoke. This phase adds a self-contained read-only workload that, after the
same source and package pins pass, runs:

- the full canonical 220-case package-only diagnostic replay;
- a direct model-local 4M intake probe;
- the 2M/4M retrieval diagnostic;
- OpenCode and DeepSeek Harness client smoke when those tools are installed;
- before and after RAM/VRAM reserve checks, with a nonce-bound receipt.

The workload is `tools/run_5060ti_current_package_verification.ps1`, and the
manifest builder can select it with
`--workload wrench_current_package_verification`.

## Verification

- Commit: `56dd8ef75f385ec57a3e99792c4340cebd6ca128`
- Full regression: `203 passed, 18 warnings`
- Manifest: `D:\models\wrench-5060ti-full-verification-20260921-01.json`
- Manifest SHA-256: `50D2DB9AF7D268B63C47F2BED006DC8F94120AE141FD0CD742CB50A6BCA1FD1D`
- Job ID: `wrench-5060ti-full-verification-20260921-01`
- Claim nonce: `7d95be8bf41245c1a60895c5406d4c81`
- HF revision: `9c6303c2c17a3798a134388c7e544728b22bd481`

The job was not accepted by the Drive upload connector. The verified queue
folder discovered by listing `jobs` was `16Cyxb70EcN5hBhDaEjNdDaKmi44d4Wvv`,
but both folder metadata and upload returned Google Drive `404 Not Found`.
Therefore the manifest is local only and there is no 5060Ti execution claim.

## Boundary

The 220 run in this workload is package-only diagnostic evidence because raw
teacher traces are not uploaded to the worker. It cannot establish teacher
parity, dense-native 4M attention quality, or production readiness. A missing
Drive handoff is an operational blocker for independent hardware evidence, not
a failed model benchmark.
