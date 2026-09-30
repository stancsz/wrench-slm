# Iteration 165: Qwen3.5-4B fit launch admission failure

- Planned fit job: `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-FIT-20260928-01`
- Observation time: 2026-09-29 UTC
- Result: **NO FIT STARTED**

The initial launch exited with code 1 at the trainer's runtime bootstrap,
before its reservation check, job claim, resource monitor, model load, or
artifact creation. Exact error: `WRENCH_LORA_ADDONS must identify the approved
add-on directory`. The command omitted the required environment variable.
The runner returned before the fit job initialized; the candidate, fit log,
scratch directory, and claim path remained absent. No model or tokenizer was
loaded and no optimizer step occurred. This is an invocation setup error, not
a training result.

The corrective launch environment must set
`WRENCH_LORA_ADDONS=C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons`,
which the trainer itself resolves and compares with its pinned approved path.
The fit still requires the same final exact receipt-hash comparison, active
2,000,000,000-byte reservation, at least 5 GiB destination headroom, and fresh
25% RAM / 10% RAM and VRAM admission. Preserve this report as evidence of the
rejected pre-run invocation.
