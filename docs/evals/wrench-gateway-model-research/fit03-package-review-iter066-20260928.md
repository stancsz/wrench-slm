# Fit 03 exact-package static review, iteration 066

Assignment: `WRENCH-FIT03-EXACT-PKG-REVIEW-ITER066-20260928`  
Nonce: `0e0e9778-2111-4136-a518-b445ad0ebd8c`  
Disposition: **PASS for the reviewed static package. Fit launch remains blocked until its live admission gates pass.**  
Scope: exact-hash static review only. This is not fit authorization.

## Identity check

Git HEAD before and after reading: `af01304824f079a64b6c3902397a2034b843511a`.
Every assigned file hash matched before and after reading:

| File | SHA-256 |
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

## Findings

No static blocker was found for one bounded fit after all admission gates pass.

- **Fit bounds and data boundary:** In `tools/train_gateway_lora_screen_02_gpu.py`, constants `EXPECTED_TRAIN_EXAMPLES`, `EPOCHS`, `GRAD_ACCUMULATION`, and `EXPECTED_FIT_OPTIMIZER_STEPS`, plus `_run_main` and its fit loop, bind the candidate to 256 train rows, 64 dev rows, three epochs, accumulation eight, and exactly 96 updates. The CLI admits only `softmax-attention-only`; instantiated targets and trainable parameter count are rechecked. The manifest-controlled train/dev paths are constrained beneath the approved dataset root and read through bounded, confined handles with pinned size and digest checks. The trainer reads the held-out digest only as manifest metadata and sets `heldout_opened_by_runner` false; the held-out payload is not opened by the training path.
- **Preflight and resource receipts:** `verify_successful_preflight` requires the successful attention-only preflight identity, matching runner/protocol/model/data/runtime/GPU fields, a released preflight reservation, and the hash-bound resource log with all samples above 10% RAM/VRAM and within the scratch cap. The supplied preflight-05 manifest and log match the pinned hashes and show one step over eight examples, 24 expected targets, 540,672 trainable parameters, 10.9850% minimum RAM, 54.4663% minimum VRAM, and zero scratch. Its observed start RAM was 17.50%, below the distinct fit-start threshold, so it does not satisfy or waive that threshold.
- **Fit admission, monitoring, and output:** `_run_main` rejects a fit below 25% free RAM before claiming or creating fit artifacts, requires the fit reservation and reservation-plus-5-GiB destination headroom, and rechecks them at update boundaries. `ResourceMonitor`, `checked_optimizer_step`, and finalization enforce the 10% RAM/VRAM floors, finite updates, scratch/log caps, exact 96-step completion, staged adapter size, and matching file inventories. `finalize_adapter_no_replace` avoids replacing an existing candidate. The candidate remains inactive.
- **Scorer and held-out boundary:** In `tools/score_gateway_lora_screen_02.py`, `verify_fit03_candidate_identity` and `verify_training_and_inputs` bind the fit-03 job, reviewed trainer source and snapshot, exact ordered 24-module list, 540,672 parameters, fit mode, and 96 completed steps. The scorer validates the training resource-log hash and floors and pins model/adapter trees. `run_score` loads the base and adapter and records the exclusive global access marker before the first held-out content read; the protocol identifies that read at scorer line 1778. References are parsed from the same held-out buffer only after prediction files are hashed. The scorer also requires the separate development-only preflight and fresh evaluation reservation before any held-out attempt.
- **Focused checks:** The assigned tests cover profile selection, the 96-step constant, destination headroom, no-reuse claims, and rejection of trainer/snapshot/target/mode/step mismatches. Tests were read but not executed, per the command restriction.

## Remaining operational gates

- **Fit-start RAM is currently a blocker:** Lowest live review sample was 4,828,648 KiB free of 33,486,624 KiB, about 14.4%. The required fit-start fraction is 25%, so a fit must not start on this sample. This sample remained above the 10% review/runtime floor. The preflight's own lowest sample was 10.9850%, also above 10% but not a substitute for fit admission.
- **Runtime reserve:** Recheck immediately before and throughout the fit; maintain at least 10% system RAM and VRAM. Lowest live VRAM sample during review was 15,211 / 16,311 MiB free. Static review cannot predict fit-time minima.
- **Storage and destination disk:** This review did not run the storage checker or inspect disk free space because those commands were outside the allowlist. Before fit, run storage status, obtain the fresh unique 1,500,000,000-byte fit reservation, account for peak growth below the 50 GB aggregate ceiling, and verify destination free space is at least reservation plus 5 GiB. The trainer repeats the reservation/headroom checks at admission and update boundaries.
- **Scorer remains a later gate:** After a completed fit and released fit reservation, obtain a fresh scorer evaluation reservation and run only the separate development-only scorer preflight. Keep held-out access closed until that preflight passes and the scorer's exact identities remain unchanged. This review authorizes neither that work nor held-out scoring.

## Review limits and next action

Only the assigned twelve files were read and hash-checked. No held-out payload or other dataset payload was opened. No tests, model/runtime loading, training, inference, benchmark, packaging, network/provider request, credential access, WSL/Docker change, or unrelated file access occurred. No source file was modified. The only write is this report.

Next action: wait for a fresh live sample at or above 25% free RAM, then perform fresh storage and destination-space admission before the one bounded fit. Preserve the 10% RAM/VRAM floors throughout. If any reviewed identity changes, obtain a new exact-hash review first.
