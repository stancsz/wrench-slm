# Iteration 045: Qwen2.5-Coder-7B inventory and QLoRA fit screen (2026-09-27)

## Result

Completed the exact public inventory for `Qwen/Qwen2.5-Coder-7B-Instruct` at
revision `c03e6d358207e414f1eca0bb1891e29f1db0e242`: all 14 files total
15,242,807,397 bytes. The report lists each metadata file and shard, plus the
four shard SHA-256 values. No model was downloaded or selected.

The candidate is a code-specific 7.61B causal model. Official Qwen QLoRA
profiles for a related 7B model report 12.3 GB peak GPU memory at 1,024 tokens
and 13.9 GB at 2,048 tokens on A100 80GB. This makes a short-context run on a
16,311 MiB RTX 5060 Ti plausible, not proven. The exact architecture, GPU,
software stack, and available system RAM still require a local preflight.

The installed Wrench trainer is Qwen3.5-specific and FP32. The current Wrench
runtime/add-on paths lack `bitsandbytes`, so a candidate-specific QLoRA runner
and pinned dependency inventory are required. Current RAM is 10.08% free, well
below the 25% fit start gate and too close to the 10% operating floor for a
runtime job. No download, dependency installation, test, inference, training,
benchmark, SubRoute POST, or provider spend occurred.

See the [candidate feasibility report](../../reports/wrench-gateway-model-research/qwen25-coder-7b-fit-feasibility-20260927.md)
for complete inventory, storage projection, compatibility gaps, source links,
and the proposed bounded preflight.
