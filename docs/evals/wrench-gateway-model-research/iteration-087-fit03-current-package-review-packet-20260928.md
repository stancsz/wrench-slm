# Iteration 087: Fit-03 exact-package review packet

Date: 2026-09-28 (America/Edmonton)  
Assignment ID: `WRENCH-FIT03-EXACT-PACKAGE-REVIEW-ITER087-20260928`  
Nonce: `6e9d8f6b-0d76-4419-9c08-76c52b377c4e`  
Status: **packet prepared; do not dispatch until RAM has safe margin above 10%**  
Repository: `C:\Users\stanc\github\wrench-slm`  
Expected HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Expected active gateway-goal SHA-256: `225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Assignment

Independently re-review the exact current Fit-03 package identity and the
scope of the current gateway-goal additions. Confirm that the appended
Iteration 083 hash reconciliation, Iteration 084 power sensitivity, and
Iteration 085/086 admission records do not alter Fit-03's synthetic-only
objective, 25% free-RAM start gate, 10% RAM/VRAM runtime floor, 96-step cap,
train/dev-only boundary, sealed held-out gate, or inactive-candidate rule.
This is a static identity/scope review, not source-code validation and not
execution authorization. Return HOLD on any changed pin, ambiguous scope,
inadequate host reserve, or output collision.

## Current identity pins

The parent re-hashed all 12 identities at HEAD above. Verify these values
again before and after the review. The first 11 non-goal identities match the
Iteration 083 package; the current goal pin is the current automation pin.

| Identity | Expected SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `tests/test_gateway_lora_profiles.py` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` |
| `tests/test_gateway_lora_screen_02_scorer_binding.py` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` |
| `docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F` |
| `docs/evals/wrench-gateway-model-research/iteration-008-preflight-05-20260927.md` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` |
| `docs/evals/wrench-gateway-model-research/iteration-009-scorer-fit03-review-20260927.md` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\resources.jsonl` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` |

## Allowed scope and commands

Read only `AGENTS.md`, `GOAL.md`, the current gateway goal above, the two
Fit-03 protocols above, and Iterations 008, 009, 083, 084, 085, 086. Do not
open any train, dev, or held-out payload. Do not read model weights, access
credentials, call SubRoute/provider endpoints, run tests, import a model,
train, infer, benchmark, package, change service configuration, or alter any
identity file.

Allowed commands only:

1. `git rev-parse HEAD` before and after.
2. `Get-FileHash -LiteralPath <one of the 12 exact paths above> -Algorithm SHA256` before and after, for all 12 paths.
3. `Get-Content -LiteralPath <one of the specifically allowed review documents above>`.
4. `Get-CimInstance Win32_OperatingSystem` and
   `nvidia-smi --query-gpu=name,memory.free,memory.total --format=csv,noheader`
   before, during, and after. Keep both RAM and VRAM free at or above 10%.

No retries. Timeout: 10 minutes. If free RAM approaches 10%, stop reading and
return HOLD without affecting any process. Do not terminate applications,
services, Docker, or WSL. The parent must run a fresh storage status and
reserve at least 25,000 bytes for this review, with SubRoute and automation
included, immediately before dispatch.

## Output and response schema

The only allowed output file is
`docs/evals/wrench-gateway-model-research/iteration-087-fit03-current-package-review-20260928.md`.
Write it only after the parent confirms the reservation and safe RAM margin.
Report: assignment ID and nonce; HEAD before/after; 12 before/after hashes and
match status; files read; resource minimums; scope disposition PASS/HOLD;
limitations; and a statement that no training, inference, tests, provider
calls, or held-out reads occurred. A PASS authorizes no execution by itself.
