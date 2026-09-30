# Iteration 082: Fit-03 current package identity review

Date: 2026-09-28 (America/Edmonton)

Job ID: `WRENCH-FIT03-PACKAGE-REVIEW-ITER082-20260928`  
Nonce: `56e5d6cb-1ad7-4f3e-8808-53e99bb225ca`  
Repository: `C:\Users\stanc\github\wrench-slm`  
Expected HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Result

**Exact package review does not pass.** HEAD matched before and after. Eleven of the twelve supplied identities matched their expected SHA-256 before and after review. The GPU protocol file did not: observed SHA-256 was `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5`; supplied expected value was `EDAA9A20E66E18F005420B3F797EED085B002BBE9AD266A5E75EE12DACE33B5`. Treat the Fit-03 package as **not currently exact-hash reviewed** until the authoritative pin is reconciled and a fresh review covers the exact identity. No package file was changed.

## Identity table

“Before” and “after” are SHA-256 values from the two bounded Get-FileHash passes.

| Identity | Before | Expected | After | Match |
| --- | --- | --- | --- | --- |
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | yes |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | yes |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | yes |
| `tests/test_gateway_lora_profiles.py` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | yes |
| `tests/test_gateway_lora_screen_02_scorer_binding.py` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | yes |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` | `EDAA9A20E66E18F005420B3F797EED085B002BBE9AD266A5E75EE12DACE33B5` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` | **no** |
| `docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | yes |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `D89487E2E880FB7F22360AEC9327DB1B370D3792B5B1D3041FEA79927B285E88` | `D89487E2E880FB7F22360AEC9327DB1B370D3792B5B1D3041FEA79927B285E88` | `D89487E2E880FB7F22360AEC9327DB1B370D3792B5B1D3041FEA79927B285E88` | yes |
| `docs/evals/wrench-gateway-model-research/iteration-008-preflight-05-20260927.md` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | yes |
| `docs/evals/wrench-gateway-model-research/iteration-009-scorer-fit03-review-20260927.md` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | yes |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | yes |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\resources.jsonl` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | yes |

## Scope finding: Iterations 080/081 and Fit-03 gates

The inspected Iteration 080/081 additions document local snapshot verification, GET-only SubRoute/model inventory checks, resource observations, and unresolved routing/storage issues. They do not alter Fit-03''s synthetic-only train/dev data boundary, objective, authorization scope, 25% free-RAM start gate, 10% RAM/VRAM runtime floors, or prohibition on held-out access during training. The current goal and protocols retain those gates. Fit-03 remains conditional on fresh exact-hash review and live storage/resource admission. This is a documentation-scope finding only and does not authorize Fit-03.

## Resources

The delegation payload''s pre-review sample was RAM 3,736.9 / 32,701.8 MiB free (11.43%) and VRAM 15,199 / 16,311 MiB free (93.18%). No separate later resource command was in the permitted command set, so no additional sample is claimed. The review was static and completed without model loading, inference, training, benchmarking, network/provider calls, or held-out payload inspection.

## Commands

1. `git rev-parse HEAD` before the identity pass.
2. `Get-FileHash -Algorithm SHA256 -LiteralPath <identity>` for exactly the 12 listed identities, before review.
3. `Get-Content -Raw -LiteralPath <allowed document>` for AGENTS.md, GOAL.md, the two protocols, and the permitted Iteration 066/079/080/081 documentation. A supplied 066/079 filename did not exist at the attempted paths; no path search was performed.
4. `git rev-parse HEAD` after document review.
5. `Get-FileHash -Algorithm SHA256 -LiteralPath <identity>` for exactly the same 12 listed identities, after review.
6. `Set-Content -LiteralPath docs/evals/wrench-gateway-model-research/iteration-082-fit03-current-package-review-20260928.md` to write this bounded report.

No tests, model operations, provider/network calls, or service mutations were performed.

