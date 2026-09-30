# Iteration 161: Qwen3.5-4B preflight attempt 02

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-PREFLIGHT-20260928-02`
- Disposition: **FAILED before optimizer step or adapter output.** This is evidence about model loading, PEFT target matching, and a data/tokenization contract failure, not a trained model or quality result.
- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
- Active gateway goal hash: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`
- Trainer SHA-256: `451C89DD972086312EC69F5DF586B10C9809E679FD41E7804E488AD85B7C05BB`
- Protocol SHA-256: `232365B9ADBD8995EA57D6DE410D2D55BACD241A0039E4F70E9A2D35AD1C8D33`
- Model: `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`

## What the attempt demonstrated

The pinned Windows runtime loaded the local BF16 model on the RTX 5060 Ti. PEFT matched exactly 32 configured q/k/v/o modules on the eight full-attention layers and excluded other modules from the target list. The manifest counted 4,540,838,400 total parameters and 1,572,864 trainable LoRA parameters (0.034638% of total). The local tokenizer and model load completed.

The attempt then stopped while tokenizing the first permitted synthetic training row, `train-evidence_select-0043`, with `ValueError: chat-template prefix mismatch`. The script independently tokenizes the user-facing prompt with `add_generation_prompt=True` and the full conversation with the assistant answer, then assumes the prompt token IDs must be a prefix of the full token IDs. That assumption failed for this pinned tokenizer. The manifest is `FAILED`; `heldout_opened_by_runner` is false; `output_dir` is null; runtime scratch peak is zero. No optimizer step, inference/generation, adapter save, or provider request occurred.

This is a second distinct trainer defect after attempt 01's tokenizer initialization ordering bug. Preserve attempt 02 as failed evidence. Diagnose the exact pinned-template serialization and token boundary using only approved train/dev rows before creating attempt 03; do not weaken the failure check by blindly slicing or suppressing the mismatch.

## Preserved outputs

| Output | Bytes | SHA-256 |
|---|---:|---|
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-preflight-02\run-manifest.json` | 5,989 | `784D981D8003A6F07EB73BB335AF83AF5057144D58B980310773A6B2FCAB06F3` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-preflight-02\resources.jsonl` | 46,650 | `E545900B3902E23EFF4A4254CBC1EB7267AFFAE325CAB77B511E92C652033803` |

The manifest binds the resource-log SHA-256 `e545900b3902e23eff4a4254cbc1eb7267affae325cab77b511e92c652033803`, trainer SHA-256 `451c89dd972086312ec69f5df586b10c9809e679fd41e7804e488ad85b7c05bb`, protocol SHA-256 `232365b9adbd8995ea57d6de410d2d55bacd241a0039e4f70e9a2d35ad1c8d33`, data-manifest SHA-256 `11683129106ff2448930818d6631b8e76201798893e7587ecb0872cbf6bcebed`, train SHA-256 `22f45c8b51ef680f9d05e8c42243ebb34e9f596b22d76577c64e371d272a39d2`, dev SHA-256 `ee0f6de198cb1d6c6b4ea19a138ccda9f0d9f1562232430a0a9ce15307760aa7`, model inventory SHA-256 `30b09cf32f06fae5418a0b925820202bfddf9e1c2a1f009d12e6396d10aed15a`, and config SHA-256 `ddc63e1c717aafa86c865bb5e01313d89d72bb53b97ad4a8a03ba8510c0621670`.

## Resource envelope

Logged minimum free RAM fraction was 15.75%; logged minimum VRAM free fraction was 39.27% (6,405/16,311 MiB). No 10% floor breach was recorded. Run window was 2026-09-29 05:25:40.234973 to 05:28:10.587261 UTC. The system returned to about 22.7% free RAM and about 6.4 GiB free VRAM immediately after exit.

## Gates before any next attempt

1. Explain and independently verify why prompt token IDs are not a prefix of the fully serialized conversation. Establish a safe target-mask boundary from the pinned tokenizer's actual chat-template behavior; check that assistant target tokens remain intact and no prompt content is trained as target.
2. Change the trainer to a new exact hash and use a distinct attempt-03 job ID, claim path, and log path. Refresh the independent source review against that package.
3. Obtain a new exact 250,000,000-byte storage reservation, destination-space check, and fresh >=10% RAM/VRAM admission. Preserve attempts 01 and 02 unchanged.
4. A full 96-step fit still requires a successful matching preflight and >=25% free RAM at fit start, plus >=10% RAM and VRAM throughout.

## Claims not established

This preflight does not establish LoRA quality, task success, coding ability, sustained all-day reliability, Frontier-token savings, 95/5 routing, or cost savings. No Frontier API was called and no provider usage was observed.
