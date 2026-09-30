# Iteration 066: verify preflight identity and prepare the fit review

Timestamp: 2026-09-28 03:49 UTC (2026-09-27 America/Edmonton)

Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Fresh admission

The latest host sample measured 2,964.2 / 32,701.8 MiB free RAM (9.06%),
15,232 / 16,311 MiB free VRAM on the NVIDIA GeForce RTX 5060 Ti, and
140,502,839,296 bytes free on C:. The Wrench process query found no active
training, inference, test, or benchmark process. RAM remains below the 10%
hard floor and well below fit 03's 25% start gate; no runtime, test, model job,
or delegation ran.

Storage was `WITHIN_LIMIT` at 10,991,474,876 bytes actual and 8,103,000 bytes
in active reservations before this report reservation. This documentation
job reserved 150,000 bytes under
`WRENCH-PREFLIGHT-IDENTITY-RECHECK-ITER066-20260928`; release it after the
report and goal update are accounted.

## Preflight receipt identity check

Re-read the preflight-05 run manifest and recomputed its manifest/resource-log
hashes. The manifest is `PREFLIGHT_COMPLETED`, with one finite optimizer step
on eight synthetic training rows, 24 attention-only targets, and 540,672
trainable parameters. Its resource log records minimum free RAM of 10.9850%,
minimum free VRAM of 54.4663%, zero runtime scratch, no adapter output, and no
heldout access. This remains a compatibility receipt only.

The current trainer and protocol hashes still match the manifest's pinned
runner and protocol identities. Current scorer and pinned-tree helper hashes
also match the earlier scorer-binding review. Preflight 05 therefore does not
need to be repeated for this unchanged code/model/runtime identity. It does
not satisfy the separate fresh package review of the current goal and updated
Iterations 008/009, and it does not waive fit 03's 25% RAM start gate.

| Review input | Current SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `tests/test_gateway_lora_profiles.py` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` |
| `tests/test_gateway_lora_screen_02_scorer_binding.py` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` |
| `docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `2FE4368C6039695F469CF9DCBC4FD98394D7F5525601D7A029896D70CB801DA9` |
| `docs/evals/wrench-gateway-model-research/iteration-008-preflight-05-20260927.md` | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` |
| `docs/evals/wrench-gateway-model-research/iteration-009-scorer-fit03-review-20260927.md` | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\run-manifest.json` | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` |
| `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-02-preflight-05-attention-only\resources.jsonl` | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` |

## Bounded independent review packet for the next admitted window

The exact review assignment is prepared but was **not dispatched**, because
free RAM is below 10%. When a fresh sample clears that floor with reserve
headroom, dispatch exactly one independent static reviewer:

- Job ID: `WRENCH-FIT03-EXACT-PKG-REVIEW-ITER066-20260928`
- Nonce: `0e0e9778-2111-4136-a518-b445ad0ebd8c`
- Expected repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
- Objective: verify the exact-hash fit-03 trainer/scorer/protocol/data-read
  boundary and fit receipt checks; identify blockers to a bounded, non-heldout
  fit. Confirm each assigned hash before/after reading and return PASS or
  BLOCKED with evidence. Do not modify source or inspect heldout contents.
- Allowed scope: the twelve files in the table above, by exact path and hash;
  source reads and file hashing only. No tests, runtime, model loading,
  inference, training, network/provider calls, credential reads, or other file
  writes.
- Output, if admitted and review completed: one report at
  `docs/evals/wrench-gateway-model-research/fit03-package-review-iter066-20260928.md`.
  Before dispatch, the orchestrator must run storage status/reserve for the
  review report and confirm destination headroom. The reviewer must preserve
  at least 10% RAM and VRAM throughout and stop if either reserve is threatened.
- Timeout: 20 minutes; no automatic retry. Response: status; files and
  before/after hashes; findings and severity; confirmation that no heldout,
  model, provider, test, or runtime action occurred; next action.

Only after a fresh independent PASS and a fresh live sample of at least 25%
free RAM may the existing fit-03 attempt be considered. Reuse the valid
preflight-05 receipt; do not rerun it unless its pinned code/model/data/runtime
identity changes. Fit still needs a fresh 1.5 GB storage reservation, 5 GiB
destination headroom beyond that reserve, and 10% RAM/VRAM throughout.

The ACTIVE hourly heartbeat remains the mechanism for subsequent checks. No
SubRoute generation was made; the configured `http://127.0.0.1:4000` route
remains closed to paid traffic without the separate spend cap and hard caller
ledger. The Wrench LoRA's decision quality, 95/5 operation, token/cost
savings, and sustained engineering remain unproven.
\n
