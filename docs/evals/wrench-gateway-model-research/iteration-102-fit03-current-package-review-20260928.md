# Iteration 102: Fit-03 current package review

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-FIT03-REFRESH-REVIEW-102-20260928`  
Nonce: `5b982777-c562-44c9-82a0-7cb411025e72`  
Repository: `C:\Users\stanc\github\wrench-slm`  
Expected HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Current goal expected SHA-256: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Decision

**PASS for the static Fit-03 package as a synthetic-only 0.8B control/feasibility diagnostic. This is not execution authorization.**

The refreshed goal identifies Qwen3.5-2B as the leading controller hypothesis, while retaining Qwen3.5-0.8B as the smallest control. The reviewed package remains scoped to that 0.8B control; it cannot establish that 0.8B is the best model, prove real workflow efficacy, or prove the 95% savings targets. Its synthetic-only train/dev plan is consistent with the current experiment boundary.

The Fit-03 runner, scorer, focused tests, and protocols match the 12 specified identities before and after review. Static inspection found the configured 256 train / 64 dev synthetic split, exactly 96 optimizer steps (three epochs, gradient accumulation 8), no held-out read in the trainer, inactive candidate output, and bounded authority. The trainer requires a fresh Fit reservation, >=25% free RAM at fit start, and >=10% RAM and VRAM throughout. It has fixed candidate, log, claim, and staging/final adapter paths, plus minimum destination headroom. The scorer has a separate held-out lock and marker path and requires completed-fit and dev-only preflight evidence before held-out scoring.

The completed preflight-05 receipt is metadata for one optimizer step on eight synthetic examples, with no adapter saved and no held-out row opened. It records 10.985% minimum free RAM and 54.466% minimum free VRAM. This is compatibility evidence only, not a full-fit capacity or quality result.

## Identity checks

HEAD before and after was `af01304824f079a64b6c3902397a2034b843511a`.

| Identity | Before SHA-256 | Expected SHA-256 | After SHA-256 | Match |
| --- | --- | --- | --- | --- |
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | yes |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | yes |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | yes |
| `tests/test_gateway_lora_profiles.py` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | yes |
| `tests/test_gateway_lora_screen_02_scorer_binding.py` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | yes |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` | yes |
| `docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | yes |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95` | `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95` | `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95` | yes |
| `docs/evals/wrench-gateway-model-research/iteration-008-preflight-05-20260927.md` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | yes |
| `docs/evals/wrench-gateway-model-research/iteration-009-scorer-fit03-review-20260927.md` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | yes |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | yes |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\resources.jsonl` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | yes |

## Scope and engineering checks

- The runner pins Qwen/Qwen3.5-0.8B revision `2fc06364715b967f1860aea9cf38778875588b17`, 256 synthetic train examples, 64 synthetic dev examples, three epochs, accumulation 8, and an exact 96-step cap. Train and dev are read through pinned bounded inputs; the trainer does not open the held-out split. The dataset manifest is marked `synthetic_only: true`; held-out is separately sealed pending the scorer's independent gates.
- The adapter is written as an inactive candidate under `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-02\fit-03-attention-only\adapter`, with staging at `...\adapter-staging`; the run log is `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-fit-03-attention-only`. The fixed fit job ID is `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN`; the claim root is `C:\wrench-slm-data\cache\gateway-lora-screen-02-claims`. Finalization uses no-replace rename; the protocol prohibits activation.
- The base inventory metadata lists 13 files totaling 1,769,980,465 bytes, pinned to the revision above. The large safetensors LFS pointer identity is explicitly recorded as not recomputed by that inventory metadata. This review did not read model weights.
- The runner enforces 10% RAM/VRAM runtime floors and 25% fit-start free RAM. Fit reservation minimum is 1,500,000,000 bytes; destination must retain that reservation plus 5 GiB operating headroom. The protocol requires a fresh aggregate storage status/reservation, accounted peak duplication and cache/log/temp/output growth, and destination-volume check. Review reservation is not a Fit reservation.
- The trainer is offline, deterministic/bounded, and does not grant shell, credential, arbitrary code mutation, or permission authority. It writes only the declared bounded candidate and receipts.
- Fit-03 scoring is separately gated; the scorer pins the exact trainer identity, target modules and 96-step receipt, requires dev-only preflight before opening held-out, then uses a one-shot lock and access marker. This static review does not authorize or perform held-out scoring.

## Resources and next gate

Resource snapshots obtained during review:

| Sample | RAM free | GPU free |
| --- | ---: | ---: |
| Start | Sampled, but numeric output was captured by the shell guard and not retained; no percentage is claimed. | Same sample command ran; value not retained. |
| Mid | 27.43% (approx. 8.9 GiB) | 15,216 / 16,311 MiB (93.29%) |
| End | 28.22% (approx. 9.0 GiB) | 15,218 / 16,311 MiB (93.30%) |

No sample showed a resource breach; the unretained start measurement is a reporting limitation. Re-sample immediately before any job. The task's 10% floors must be maintained throughout. Before Fit-03, recheck live storage status with all linked roots, obtain a distinct >=1.5 GB fresh fit reservation covering peak duplicates, verify destination free space >= reservation + 5 GiB, recheck >=25% free RAM and >=10% RAM/VRAM at launch, and confirm the preflight reservation is released and receipt remains valid. Stop before artifact creation if any gate fails.

## Reviewed files and limits

Read: `AGENTS.md`; `docs/goal/wrench-gateway-model-research/GOAL.md`; both Fit protocols; Fit-03 trainer and scorer; focused profile and scorer-binding tests (read only); Iterations 008, 009, 083, and 087 where available; the Qwen candidate metadata; local model inventory metadata; synthetic dataset manifest; and preflight-05 run/resource metadata. Exact 12 hashes above were checked before and after, with HEAD before/after.

No training/dev/held-out payload, model weight contents, credentials, or provider data were read. No tests were run. No inference, training, benchmarking, packaging, model loading, provider/API/network calls, storage mutation, or SubRoute interaction occurred. No Fit output was created.

