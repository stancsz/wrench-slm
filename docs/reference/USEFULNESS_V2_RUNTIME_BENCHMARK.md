# Usefulness V2 packaged runtime benchmark

Updated: 2026-09-10

This benchmark measures the immutable V21 package on a bounded 22-case slice
of the V2 development population. It is separate from quality scoring and does
not change the V21 or V22 quality decisions.

The benchmark records:

- five cold process starts with model load and one prediction each;
- three warm passes over the 22-case slice;
- p50, p95, and p99 prediction latency;
- process RSS before and after load;
- CUDA allocated, reserved, and peak memory;
- serial completions per second;
- bounded queue wait and rejected admissions for nominal loads of 2 and 4.

The model handle is accessed serially through one worker so concurrent requests
cannot race a shared model. Queue wait and admission rejection are measured;
this is not a claim of parallel GPU throughput.

Reproduce with:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\benchmark_package_runtime.py `
  --data data\pilots\usefulness-v2 `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --output artifacts\model-release\v21-usefulness-v2-runtime
```

The result is a hardware- and workload-specific observation. It does not
establish CPU, Pi, high-concurrency, service, or production performance.
