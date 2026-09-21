# Phase 299: bounded operational shadow

## Result

`PASS_BOUNDED_OPERATIONAL_SHADOW` for the current materialized portable package:

- package: `D:\models\_wrench-current-client-20260921`
- 4 concurrent clients, 10 rounds, 40 expected requests
- 40/40 responses completed, with only bounded `accepted` or `abstain` outcomes
- 0 model calls in mechanical-only mode
- 33/40 requests used the embedded mechanical fast path
- p50 2042.551 ms and p95 2758.79 ms across the mixed stress set
- a client socket was closed mid-request, and the next request recovered with `accepted` in 2.155 ms
- RAM availability stayed above 49 percent before and after the run
- no CUDA device was visible on this host, so VRAM reserve was not applicable

Receipt: `operational-shadow-receipt.json`

## Scope and interpretation

This is a local Gate E diagnostic slice for server concurrency, fail-closed
responses, cancellation recovery, and host resource reserve. It is not a
production approval, a quality benchmark, or an independent 5060Ti result.

The mixed request set intentionally includes a health probe that can wait for
its bounded timeout. Therefore its aggregate p95 is not the Wrench hot-path
latency. The receipt records the mechanical fast-path coverage separately.

The test never executes a proposed tool action and does not modify the package,
repository, or external service.

## Reproduction

```powershell
python tools/run_operational_shadow.py `
  --package-dir D:\models\_wrench-current-client-20260921 `
  --output phases\phase-299-operational-shadow\operational-shadow-receipt.json `
  --concurrency 4 `
  --rounds 10 `
  --timeout 5
```
