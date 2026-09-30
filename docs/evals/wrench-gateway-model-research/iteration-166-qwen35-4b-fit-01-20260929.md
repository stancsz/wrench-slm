# Iteration 166: Qwen3.5-4B synthetic LoRA fit

- Job: `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-FIT-20260928-01`
- Result: **COMPLETED**, 96/96 optimizer updates
- Candidate state: saved, inactive; no activation or routing change
- Model: `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- Fit window: 2026-09-29 06:06:30 to 06:56:10 UTC, about 49m 40s
- Trainer SHA-256: `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5`
- Protocol SHA-256: `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893`
- Independent package review: Iteration 164, conditional pass for this bounded fit; its pre-launch receipt-hash condition was checked immediately before launch

## Fit and runtime receipt

The fit used the pinned BF16 base and runtime on NVIDIA RTX 5060 Ti UUID
`GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. It trained rank-8 LoRA on 32
q/k/v/o projections in full-attention layers `[3, 7, 11, 15, 19, 23, 27, 31]`.
The frozen base has 4,540,838,400 parameters; 1,572,864 adapter parameters
were trainable (0.03464%). Only the approved synthetic split was read: 256
train and 64 dev rows, max tokenized length 338. The sealed held-out payload
was not opened.

| Epoch | Optimizer step | Mean train loss | Dev loss | Last gradient norm |
|---:|---:|---:|---:|---:|
| 1 | 32 | 0.3644025 | 0.0720415 | 0.9639687 |
| 2 | 64 | 0.0041381 | 0.0642743 | 0.3298234 |
| 3 | 96 | 0.0005542 | 0.0642282 | 0.0049065 |

The dev loss is recorded for diagnosis only; it is not a model-selection or
quality result. The very low train loss on 256 synthetic examples is compatible
with memorizing the synthetic policy and does not show repository engineering
ability or transfer.

Resource log: 2,534 one-second samples. Minimum observed free system RAM was
17.1307%; minimum free VRAM was 16.7617% (2,734/16,311 MiB). Maximum runtime
scratch was 0 bytes. A fresh post-run sample was 25.55% free RAM and
15,240/16,311 MiB free VRAM. The 10% runtime floor held in the recorded
samples. The fit reservation remained active until the process was terminal
and all outputs were inventoried.

## Exact output identities

- Manifest: `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-fit-01\run-manifest.json`, SHA-256 `D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E`.
- Resource log: same directory, `resources.jsonl`, SHA-256 `5812CD2BE242B407CBA8EFE8E04813D6973BCB2B9CD61A958849B491B7DFB781`.
- Epoch metrics: same directory, `epoch-metrics.jsonl`, SHA-256 `889F5FCA08FAA5C5845BF2C8F2168A371F91108ADBFCAD55FE28B9D384AA765D`.
- Adapter directory: `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b\fit-01\adapter`; total 6,307,540 bytes.
- `adapter_model.safetensors`: 6,300,864 bytes, SHA-256 `051A942CC306D15FF22AD300D6256CC4B8E6335B9C6263B65696353B04938E5C`.
- `adapter_config.json`: 1,280 bytes, SHA-256 `F77ECF3C2E87B2586563F3CA6017B74F62B180C31F67260A590CCFF85453531F`.
- `README.md`: 5,396 bytes, SHA-256 `D402F188EBE4AA2ABEB5929611EE4C919D4DAEE9B69751E499696F871F82DC96`.

The 2,000,000,000-byte reservation was admitted with every assigned external
root included. Final accounting reported 29,378,763,008 actual bytes and
31,384,866,008 projected bytes including active reservations, below the
50,000,000,000-byte limit. The C: destination had 123,615,772,672 free bytes
after fit.

## Limits and next steps

This is a completed synthetic LoRA fit and a useful host feasibility result.
It does not prove the adapter improves task outcomes, 95% local completion,
5% frontier routing, 95% frontier-token reduction, 95% cost reduction, or
all-day engineering. No Frontier API was called, so no billed-token savings
were measured. During this run, `causal_conv1d` and `flash-linear-attention`
were unavailable and the corresponding Qwen operations used PyTorch fallbacks;
the fit took about 49m 40s. This runtime is not an inference-throughput or
all-day usability result.

Next, keep the adapter inactive and prepare a separately reviewed, answer-blind
dev evaluation with exact output/model/data identities and resource/storage
admission. Compare the LoRA against the frozen base and deterministic Wrench
on the same synthetic dev episodes. Do not open held-out data until a separate
review explicitly admits it. Evaluate against the existing 2B and 0.8B
evidence before updating the provisional parameter-size recommendation.
