# Phase 199: v81 compact-lookup package regression

Date: 2026-09-20

## Package

`D:\models\Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v81-compact-lookup-fix`

v81 includes the v80 bounded lookup evidence window plus the compact-payload
boundary fix caught by the full regression suite. Structural validation passed.

## Regression receipts

The package-local HTTP endpoint was exercised with client mechanical fast-path
bypass and an isolated deterministic health fixture.

### 220-case replay

- status: `PASS_MECHANICAL_WORKER`;
- weighted coverage: `96.2576%`;
- net savings: `96.1611%`;
- Wrench-plus-fallback weighted success: `99.6767%`;
- teacher weighted success: `70.7422%`;
- Wrench-plus-fallback median / p95: `194.680 ms` / `356.599 ms`;
- fallbacks: `5`;
- prohibited accepts: `0`;
- unexpected mutations: `0`.

### Sealed 44-row final slice diagnostic

- status: `PASS_MECHANICAL_WORKER`;
- weighted coverage and savings: `100%` / `100%`;
- Wrench-plus-fallback weighted success: `100%`;
- teacher weighted success: `88.9922%`;
- median / p95: `203.554 ms` / `344.058 ms`;
- fallbacks, prohibited accepts, and unexpected mutations: `0`.

### 2M/4M retrieval

The direct package retrieval probe remained `PASS_PACKAGE_RETRIEVAL_2M_4M`,
with 6/6 exact needle recoveries, zero model calls, and worst single-run
latency `16.972 ms`.

Raw receipts are in `package-validation.json`, `package-retrieval-quality.json`,
`replay-220/`, and `replay-final/`.

## Boundary

This is the strongest current bundled hybrid diagnostic. It is not a final
family-disjoint approval, current-commit 5060Ti receipt, dense-native quality
claim, or production enablement decision.
