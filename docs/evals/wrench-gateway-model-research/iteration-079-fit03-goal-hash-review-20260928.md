# Iteration 079: Fit-03 package identity after the goal update

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-FIT03-GOAL-HASH-REVIEW-ITER079-20260928`

Nonce: `1f15aebc-6e44-4f09-9c31-0d705c81d2b7`

Disposition: **PASS** for current static package identity and the reviewed
documentation scope. This is not Fit-03 authorization.

## Identity review

The prior Fit-03 package review included the research goal file among 12
hash-bound identities. Iteration 078 updated that file, making the earlier
goal hash stale. The independent reviewer rechecked the identities at Wrench
HEAD `af01304824f079a64b6c3902397a2034b843511a` before and after review.

| Identity | Prior SHA-256 | Current SHA-256 | Result |
| --- | --- | --- | --- |
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` | Match |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` | Match |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` | Match |
| `tests/test_gateway_lora_profiles.py` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` | Match |
| `tests/test_gateway_lora_screen_02_scorer_binding.py` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` | Match |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BBE9AD266A5E75EE12DACE33B5` | `EDAA9A20E66E18F005420B3F797EED085B002BBE9AD266A5E75EE12DACE33B5` | Match |
| `docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` | Match |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `2FE4368C6039695F469CF9DCBC4FD98394D7F5525601D7A029896D70CB801DA9` | `57A2EB77AA336196BBE917290566DB50281EFDAC645D882CA655134EE5136235` | Expected change from Iteration 078 |
| `docs/evals/wrench-gateway-model-research/iteration-008-preflight-05-20260927.md` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` | Match |
| `docs/evals/wrench-gateway-model-research/iteration-009-scorer-fit03-review-20260927.md` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` | Match |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` | Match |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\resources.jsonl` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` | Match |

The reviewer read the current `AGENTS.md`, research goal, Fit-03 and held-out
protocols, Iteration 066 review, Iteration 078 report, and the v2 architecture,
experiment, and storage/recovery documents. The reviewer confirmed the new
goal content does not change Fit-03's objective, authorization conditions,
25% RAM start gate, 10% runtime floors, train/dev boundary, or held-out gate.
This is a documentation-scope review and hash continuity for the unchanged
source identities, not a new source-code review.

## Resource gate and scope

Reviewer samples were:

| Sample | Free RAM | Free VRAM |
| --- | --- | --- |
| Before | 3,721,612 / 33,486,624 KiB (11.11%) | 15,202 / 16,311 MiB |
| During | 3,725,088 / 33,486,624 KiB (11.12%) | 15,198 / 16,311 MiB |
| After | 3,766,480 / 33,486,624 KiB (11.25%) | 15,199 / 16,311 MiB |

The 10% RAM and VRAM floors remained met. The latest RAM sample is still
4,497.2 MiB below Fit-03's 25% start gate. No tests, model loading, inference,
training, held-out reads, provider calls, or network requests were run. The
next fit action remains a fresh sample at or above 25% free RAM, followed by a
fresh storage reservation and destination-space check.
