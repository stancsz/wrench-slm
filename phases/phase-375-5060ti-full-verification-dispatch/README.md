# Phase 375: Full 5060Ti Verification Workload

Date: 2026-09-21

Status: `DISPATCHED_PENDING_5060TI_CLAIM`

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

The first Drive connector upload attempt returned `404 Not Found` even though
the folder was visible in Drive. The manifest was then uploaded through the
authenticated Drive UI and verified by Drive metadata readback:

- Drive file ID: `1iIxpVZ8TyPIjsO1P-sBpT4AA6VZ3Xl3X`
- Drive URL: `https://drive.google.com/file/d/1iIxpVZ8TyPIjsO1P-sBpT4AA6VZ3Xl3X/view?usp=drivesdk`
- Parent: `jobs/pending` (`16Cyxb70EcN5hBhDaEjNdDaKmi44d4Wvv`)
- Uploaded size: `3063` bytes

The job is now genuinely dispatched and awaiting a worker claim. There is
still no 5060Ti execution claim until the worker moves it to running and
returns the nonce-bound receipt.

## Boundary

The 220 run in this workload is package-only diagnostic evidence because raw
teacher traces are not uploaded to the worker. It cannot establish teacher
parity, dense-native 4M attention quality, or production readiness. A missing
Drive handoff is an operational blocker for independent hardware evidence, not
a failed model benchmark.
