# Gateway experiment iteration 001: synthetic corpus prepared

Date: 2026-09-27 (America/Edmonton)
Status: corpus generated and identity-bound; the authorized LoRA training run is now active
Goal: [gateway LoRA experiment](../../goal/wrench-gateway-model-research/GOAL.md)
Protocol: [LoRA screen 01](lora-screen-01-protocol-20260927.md)

## Job and storage receipt

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-01-DATA-20260927`
- Storage reservation: 10,485,760 bytes; process completed; files accounted.
- Destination: `C:\wrench-slm-data\datasets\wrench-gateway-model-research\lora-screen-01`
- Generator: [generate_gateway_lora_screen_01.py](../../../tools/generate_gateway_lora_screen_01.py)
- Generator SHA-256: `606b86d8e1f48b0aad6d7db6353665b43033a3f07c0470cd1751c8005709fa77`
- Manifest SHA-256: `11683129106ff2448930818d6631b8e76201798893e7587ecb0872cbf6bcebed`

| Split | Examples | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| Train | 256 | 375,968 | `22f45c8b51ef680f9d05e8c42243ebb34e9f596b22d76577c64e371d272a39d2` |
| Development | 64 | 93,743 | `ee0f6de198cb1d6c6b4ea19a138ccda9f0d9f1562232430a0a9ce15307760aa7` |
| Held out | 128 | 191,354 | `1cc23dcbc99890d55a447131b4d3de5cdff4cfc2116072f041d747e8953848de` |

All examples are newly generated synthetic cases in four families:
`evidence_select`, `retrieve_stop`, `compaction_policy`, and `route`. The
generator uses separate wording, identifiers, paths, revision markers and
scenario seeds by split. It contains no network/model access and does not read
old fixtures or repository content. I inspected one train row and one dev row
for schema and oracle shape. The held-out JSONL has not been opened, scored,
used for training, or used for tuning; only its emitted size and digest are
recorded here.

## What this proves

This proves the new synthetic corpus can be generated reproducibly under the
storage boundary. It does not prove LoRA compatibility, learning, routing
quality, context-token savings, frontier savings, task-value retention, dollar
savings, or coding ability. The generator's exact rule labels remain a synthetic
policy oracle rather than real outcome data.

## Current gates

The current 0.8B CPU LoRA run passed its single-step resource/compatibility
preflight and was admitted under its own 2,000,000,000-byte storage reservation.
Its live status and resource samples are recorded in
[iteration 002](iteration-002-lora-preflight-20260927.md). Do not attempt 4B
training from the current free-VRAM state.

The strong route remains blocked for generation: the owner requested the
subroute at port 4000, but the live force-mode selection is OpenRouter and the
USD spend cap is unanswered. Local work can proceed without contacting it.
