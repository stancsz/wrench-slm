# Iteration 160: Qwen3.5-4B trainer source review

- Review job ID: `WRENCH-QWEN35-4B-INDEPENDENT-SOURCE-REVIEW-ITER160-20260928`
- Nonce: `4ccca557-8165-4d50-a512-5e04ebc60f8f`
- Disposition: **CONDITIONAL for the one-step preflight only**. This review does not authorize the 96-step fit, candidate activation, provider calls, or a product claim.
- Reviewed repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
- Gateway goal hash at review: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Exact reviewed identities

| Item | SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_03_4b_gpu.py` | `56582C343C1C0E4DB4D1DB597A853677D72686D195F24D033E4D989712CC6AB4` |
| `docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-gpu-protocol-20260928.md` | `8669827AE7D4EAD882C0BDEB21DD7C0E775E999BC77D5621886C26B2FDB79E70` |
| Pinned model config | `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670` |
| Reviewed storage/runtime helper | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |

Model identity is `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; the pinned inventory records 14 files totaling 9,342,907,469 bytes. The trainer is a new BF16 path, separate from the existing 0.8B FP32 screen trainer. It targets q/k/v/o only on the 8 configured full-attention layers, excludes vision modules, freezes the foundation, and keeps its candidate inactive.

## Source review findings

No static blocker was identified for a bounded one-step preflight. The reviewed source binds the pinned tree and hashes, rejects unexpected links/reparse points, reads only the permitted train/dev inputs, checks intended adapter targets and trainable modules, and emits a receipt binding the exact runtime, GPU, target list, and parameter count. It has preflight-specific output paths and storage reservation identity, checks resource floors before heavy imports and during work, and avoids replacing existing outputs. The protocol describes a separate later fit gate, a 96-step ceiling, candidate inactivity, and no held-out access.

The preflight remains necessary because static inspection cannot establish that the installed PEFT version resolves the target modules as intended, that BF16 loading and gradient checkpointing work on this host, or that the measured peak remains within the resource floor. A successful preflight would be diagnostic evidence only, not training-quality or product-utility evidence.

## Admission conditions before preflight

1. Reconfirm these exact source and protocol hashes and the reviewed goal hash; do not modify the reviewed files without refreshing review.
2. Run the storage checker, reserve the bounded preflight peak under its unique job ID, include every external Wrench path, and confirm destination-volume free space exceeds the reservation plus 5 GiB.
3. Take a fresh RAM/VRAM sample and confirm at least 10% free throughout. Do not start if either floor is unavailable. The separate full-fit gate requires at least 25% free system RAM at fit start and is not met by this review.
4. Confirm no process or prior job owns the exact output paths; use the same live process handle if a job is already running.
5. Run only the one-step preflight. Preserve a failure receipt and release its reservation only after the process is terminal and outputs are accounted for.

## Review-time resource sample and scope

Review-time samples were about 20.36% free system RAM and 15,196 MiB free of 16,311 MiB VRAM at start; about 20.55% RAM and 15,203 MiB VRAM free at end. These samples are historical and do not substitute for a fresh admission check. The reviewer performed source inspection only: no model load, inference, fit, benchmark, tests, held-out read, provider call, credential access, SubRoute change, or file edit.

## Evidence boundary

This review does not establish measured Frontier token savings, 95% task completion, all-day coding reliability, overall best model size, LoRA effectiveness, or all-in cost savings. No provider usage is available. Existing tokenizer-based fixture reductions are local estimates and must not be described as billed Frontier-token savings.
