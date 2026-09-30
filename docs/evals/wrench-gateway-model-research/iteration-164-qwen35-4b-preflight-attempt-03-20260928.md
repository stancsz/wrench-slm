# Iteration 164: Qwen3.5-4B attempt-03 preflight

- Job: `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-PREFLIGHT-20260928-03`
- Result: **PREFLIGHT_COMPLETED**, exit code 0
- Scope: offline, one-step synthetic train preflight only; candidate remains inactive
- Model: `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- Inventory SHA-256: `30B09CF32F06FAE5418A0B925820202BFDDF9E1C2A1F009D12E6396D10AED15A`
- Config SHA-256: `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670`
- Trainer SHA-256: `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5`
- Protocol SHA-256: `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893`

## Receipt

The run tokenized 256 synthetic train rows and 64 synthetic dev rows, with a
maximum sequence length of 338. It completed one optimizer update on eight
preflight examples. Mean loss was `1.3882495611906052`; gradient norm was
`1.6025233268737793`. The instantiated adapter matched 32 q/k/v/o projection
modules on full-attention layers `[3, 7, 11, 15, 19, 23, 27, 31]`: 1,572,864
trainable parameters out of 4,540,838,400 total (0.03464%). Precision was BF16.
No candidate output was written (`output_dir=null`), and the runner reports no
held-out access.

Manifest: `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-preflight-03\run-manifest.json`, 6,033 bytes, SHA-256
`6EA37A8BA9A1B75CC1E4749085E7EB50E456BFAE039FAF6E74417EF3DCC353C4`.

Resource log: `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-preflight-03\resources.jsonl`, 49,186 bytes, SHA-256
`0629B827E4704445BF3E456B331A8C917C0B135460C019FA99C88D514A769732`.

The job started with 25.91% free RAM. Minimum observed free RAM was 19.31%;
minimum observed GPU memory was 4,144/16,311 MiB (25.39%). A fresh post-run
sample was 25.90% free RAM and 15,184/16,311 MiB free VRAM. No workload was
started below the 10% runtime floor.

## Limits and next gate

This establishes that the pinned BF16 model, runtime and adapter targets can
complete a one-step update within the observed resource floor. It does not
establish adapter quality, coding effectiveness, frontier-token savings,
95/5 routing, cost savings, or all-day engineering reliability. The run used
synthetic train/dev data only; the sealed held-out set was not opened. During
execution, optional `causal_conv1d` and `flash-linear-attention` kernels were
unavailable, so Qwen's linear-attention blocks used their PyTorch fallback.
That may reduce throughput and must be measured for a sustained-fit decision.

Iteration 163's independent source review allowed only this one-step
preflight; it explicitly did not authorize the 96-step fit. Before any fit,
obtain an independent exact-hash review of the fit package and this completed
receipt, then take a fresh storage admission with a distinct job ID, verify at
least 5 GiB destination headroom, and require at least 25% free RAM at fit
start while maintaining 10% free RAM and VRAM throughout. Keep the candidate
inactive. Do not use this synthetic preflight as product-utility evidence.
