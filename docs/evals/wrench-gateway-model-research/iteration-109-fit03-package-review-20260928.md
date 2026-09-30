# Iteration 109: Fit-03 refreshed static package review

Date: 2026-09-28 (America/Edmonton)

Assignment: WRENCH-FIT03-PACKAGE-REVIEW-ITER109-20260928
Nonce: dd4fc48e-5bd4-463d-8c4e-e326cf9b29fe
Repository: C:\Users\stanc\github\wrench-slm
Expected HEAD: af01304824f079a64b6c3902397a2034b843511a
Current GOAL.md expected SHA-256: B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027

## Decision

PASS for the static Fit-03 package as a bounded synthetic-only Qwen3.5-0.8B LoRA diagnostic candidate. This is not authorization to run the fit, select 0.8B as the final model, activate an adapter, or claim product effectiveness.

HEAD before and after review was af01304824f079a64b6c3902397a2034b843511a. All 12 assigned identities matched their expected SHA-256 both before and after review. The current GOAL.md hash matches the new assignment. Iteration 102 is stale as a goal-bound approval because it was pinned to prior goal hash D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95; this review supersedes it only for the current static package identity/scope review. Historical reports remain historical evidence.

The refreshed full goal removes a fixed model-size preference, confines training to the previously authorized sub-10B staged experiment, keeps model selection open pending hardware fit and a representative local coding-task battery, and retains 0.8B as a small control/candidate. The package remains coherent only as a synthetic diagnostic/control. It cannot be treated as the selected local coding agent or as evidence that its model-size is optimal. The full 95% completion, <=5% frontier route, >=95% frontier-token savings, >=95% all-in cost reduction, success-retention and all-day engineering criteria remain unproven and are outside this package's evidentiary reach.

## Identity results

| Identity | Before SHA-256 | Expected SHA-256 | After SHA-256 | Match |
| --- | --- | --- | --- | --- |
| tools/train_gateway_lora_screen_02_gpu.py | 62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC | 62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC | 62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC | yes |
| tools/score_gateway_lora_screen_02.py | 0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5 | 0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5 | 0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5 | yes |
| tools/wrench_windows_pinned_tree.py | E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499 | E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499 | E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499 | yes |
| tests/test_gateway_lora_profiles.py | 84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614 | 84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614 | 84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614 | yes |
| tests/test_gateway_lora_screen_02_scorer_binding.py | 3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2 | 3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2 | 3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2 | yes |
| docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md | EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5 | EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5 | EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5 | yes |
| docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md | B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B | B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B | B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B | yes |
| docs/goal/wrench-gateway-model-research/GOAL.md | B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027 | B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027 | B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027 | yes |
| docs/evals/wrench-gateway-model-research/iteration-008-preflight-05-20260927.md | 0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3 | 0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3 | 0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3 | yes |
| docs/evals/wrench-gateway-model-research/iteration-009-scorer-fit03-review-20260927.md | F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5 | F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5 | F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5 | yes |
| C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json | D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131 | D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131 | D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131 | yes |
| C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\resources.jsonl | A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1 | A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1 | A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1 | yes |

## Package gates reviewed

- Training data and schedule: protocol and runner pin the Qwen/Qwen3.5-0.8B snapshot at revision 2fc06364715b967f1860aea9cf38778875588b17; 256 synthetic train rows and 64 synthetic dev rows; train/dev only; 3 epochs with accumulation 8; exactly 96 optimizer steps. The runner never opens the held-out split. Held-out remains sealed from training/tuning and separately guarded for one-shot scoring.
- Candidate handling and authority: output is a non-activated candidate; no automatic activation or permission authority is added. The model's output is constrained to bounded decisions and does not provide arbitrary shell, credentials, or code mutation.
- Output identity and paths: fixed Fit job ID WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN; adapter output C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-02\fit-03-attention-only\adapter with a separate adapter-staging sibling; run logs C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-fit-03-attention-only; unique job claim under C:\wrench-slm-data\cache\gateway-lora-screen-02-claims. The final adapter uses no-replace finalization. Training does not create the scorer's held-out access marker.
- Resource and storage guards: runtime floors are >=10% free RAM and VRAM; fit start gate is >=25% free RAM. Protocol requires fresh aggregate storage status and a distinct Fit reservation of at least 1,500,000,000 bytes, with peak duplicate/source/checkpoint/cache/log/temp/output growth accounted, and destination free space at least the reservation plus 5 GiB. The runner checks active reservation identity and destination headroom. The admitted 10,000,000-byte review reservation is not a Fit reservation; live aggregate budget and destination admission for Fit were not rechecked in this static review.
- Preflight: prior receipt records a completed one-step attention-only compatibility check on eight synthetic training examples, with no adapter and no held-out read. It is not full-fit, inference-quality, or candidate-selection proof.
- New goal compatibility: the current full goal allows a hardware-gated model comparison and training within the existing below-10B staged scope. It says model size is not preselected; 0.8B is a small control, and a representative local coding-task battery is needed to choose the model. This package can remain as a control diagnostic but cannot satisfy that battery or elect 0.8B as the final coding model. The current full product success, token/cost, and all-day criteria remain unchanged and unproven.

## Resources

| Sample | RAM free | VRAM free |
| --- | ---: | ---: |
| Start | 21.85% | 15,198 / 16,311 MiB (93.18%) |
| Mid | 21.89% | 15,195 / 16,311 MiB (93.16%) |
| End | 21.89% | 15,195 / 16,311 MiB (93.16%) |

All three observed samples exceeded the 10% floors. Current RAM was below Fit-03's 25% start gate at these review samples, so no fit should start on this evidence. Recheck at actual Fit admission.

## Files, commands, and limits

Reviewed read-only: AGENTS.md; current GOAL.md; Fit-03 GPU training protocol; held-out scoring protocol; Iteration 008 and 009 records; Iteration 102 current-package review; Iteration 087 current-package review packet; trainer, scorer, pinned-tree helper, and the two focused profile/scorer-binding tests. The 12 pinned identities above were hashed before and after. Review was bounded to package semantics and current goal alignment.

Commands used: git rev-parse HEAD before and after; Get-FileHash -LiteralPath <each of the 12 listed identities> -Algorithm SHA256 before and after; Get-CimInstance Win32_OperatingSystem; nvidia-smi --query-gpu=name,memory.free,memory.total --format=csv,noheader; Get-Content/Select-String for the listed policy/protocol/prior-review docs; rg -n for bounded source/test gate inspection.

No tests, training, inference, benchmark, model loading, packaging, downloads, network/provider calls, credentials, payload reads, storage mutations, or SubRoute calls occurred. No package/source file was edited. The only output from this assignment is this report.

## Next gate

Before Fit execution, refresh the exact package review if any pinned identity changes; run current storage status including every linked root and admit a unique fit-specific reservation covering measured peak duplication; check destination free space, verify the prior preflight reservation is released and its receipt remains valid; then recheck >=25% free RAM at fit start and preserve >=10% RAM/VRAM throughout. A static PASS does not waive any of these checks or establish product utility.

