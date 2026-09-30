# Iteration 202: Qwen3.5-2B LoRA preflight 03 results

Date: 2026-09-29  
Disposition: **PASS for the bounded one-step GPU feasibility preflight only**  
Optimizer steps: **1**; adapter saved: **no**; held-out data opened: **no**

## Result

The revised preflight passed the exact local model inventory, loaded all 617
weight tensors, attached the reviewed rank-8 LoRA to 24 Q/K/V/O projections in
the six full-attention layers, and completed one optimizer update using the
first eight synthetic training examples. The instantiated trainable parameter
count was exactly **737,280**, matching the revised calculation. The receipt
records a diagnostic preflight loss mean of 1.8465 and gradient norm of
2.4261; these are execution diagnostics, not task-quality measurements.
`output_dir` is null, so no adapter candidate was saved.

The previous attempts explain the package changes: attempt 01 stopped before
model loading because `.cache` metadata was inside the snapshot directory;
attempt 02 loaded weights but rejected the too-narrow Q projection before any
optimizer update. The metadata is preserved outside the model root. Attempt 03
pins the Transformers Qwen3.5 modeling source that defines the packed query
and gate width, then verifies the expected matrix dimensions and parameter
count at runtime.

## Exact run identity

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-PREFLIGHT-20260929-03`.
- Base: `Qwen/Qwen3.5-2B`, revision
  `15852e8c16360a2fea060d615a32b45270f8a8fc`.
- Local model inventory SHA-256:
  `23E0D5F79E57D41AB9F007B697D8F75F56F5F528519BFDF15F406E1F28DF3DD5`.
- Candidate manifest SHA-256:
  `D4917EF337978B93D2220A9888CB4F640EDB63E54C8E49F70F0696B175DD2956`.
- Trainer SHA-256:
  `46E4F8ADED97EE0A4A524600CABFA089194767645169061D1500E9281662B3E5`.
- Protocol SHA-256:
  `6F06CF46EFE6862F8290D046E7327E79A085D3E9E05417871BBBAF00419A4B5F`.
- Qwen3.5 modeling source SHA-256:
  `762FEB6C7426A7F15B5BF830DF54C07438BF9E7C27B8CDB23179045920412C3B`.
- Dataset manifest SHA-256:
  `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED`;
  train split SHA-256
  `22F45C8B51EF680F9D05E8C42243EBB34E9F596B22D76577C64E371D272A39D2`;
  dev split SHA-256
  `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7`.
- Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0,
  PEFT 0.21.0, Accelerate 1.15.0; NVIDIA RTX 5060 Ti, UUID
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.
- Run manifest: 7,253 bytes, SHA-256
  `EC7EA892935F6435124B355236418AFF95BD790F42CEF99688730829F4308667`.
- Resource log: 30,252 bytes, SHA-256
  `A1E2802DB7E7ECBF84F7FF7368E60CEC3CF41420BF6922D8BF1CC3F5C1F3D17A`.

The fresh admission sample had 29.38% free RAM, 15,189/16,311 MiB free VRAM,
and 129,263,087,616 bytes free on C:. Across the run, minimum free RAM was
22.79% and minimum free VRAM was 8,643/16,311 MiB (52.99%). The 300,000,000
byte reservation was within the aggregate 50 GB limit. No provider call,
network access, or external routing occurred.

## Limits and next gate

This confirms only that this exact BF16 model and rank-8 adapter placement can
complete one optimizer step on this host while maintaining the 10% resource
floors. It does not establish the full 96-step fit, representative coding
quality, 95/5 local completion and escalation, Frontier token savings, lower
all-in cost, or all-day engineering reliability.

The fit is a distinct 96-step job and is not authorized by this preflight
review. Obtain a fit-specific exact-hash review, then require a fresh live
sample with at least 25% free RAM at fit start, at least 10% free RAM and VRAM
throughout, a fresh reservation of at least 2,000,000,000 bytes, and at least
5 GiB destination free space after projected writes. Keep the candidate
inactive and do not open the sealed held-out split.
