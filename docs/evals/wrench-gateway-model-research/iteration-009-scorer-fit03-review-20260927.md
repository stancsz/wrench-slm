# Iteration 009: fit-03 scorer binding review

Date: 2026-09-27 (America/Edmonton)

Status: **SCORER BINDING STATIC REVIEW PASS; FIT 03 BLOCKED BY LIVE RAM GATE; HELDOUT CLOSED**

## Scope

This iteration closes the P2 finding from the first fit-03 scorer review. It
records source identity checks and a small direct verifier check. It is not a
training or inference receipt, does not authorize heldout access, and does not
prove Wrench policy quality, coding ability, the 95/5/95 target, token or cost
savings, or sustained engineering.

## Correction

The scorer now pins the trainer source to the independently reviewed trainer
SHA-256 and requires both the saved trainer snapshot and run manifest to match
that pin. It checks the exact ordered list of 24 `self_attn` q/k/v/o targets
at layers 3, 7, 11, 15, 19, and 23, alongside the adapter profile, target
count, 540,672 trainable parameters, fit mode, non-preflight mode, and exactly
96 expected and completed optimizer steps. The checks run inside training
receipt verification before heldout marker creation; the sealed split's first
content read remains after the exclusive global marker is written.

## Independent exact-hash review

Assignment `WRENCH-GW-FIT03-SCORER-CORRECTION-REVIEW-20260927-02`, nonce
`26a51e87-1d83-44d4-a52a-40d8216f89e9`, returned **PASS**. The reviewer found
the prior P2 closed and reported no additional blocking finding. Repository
HEAD was `af01304824f079a64b6c3902397a2034b843511a` before and after. Each
assigned hash was unchanged before and after:

| File | SHA-256 |
| --- | --- |
| `tools/score_gateway_lora_screen_02.py` | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` |
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `docs/evals/wrench-gateway-model-research/heldout-eval-protocol-20260927.md` | `B9CD95EE2C271A4ADD86A93942D1D9582389687EC6F85CE69755AFE596D8717B` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A6E75EE12DACE33B5` |
| `tests/test_gateway_lora_screen_02_scorer_binding.py` | `3892726760B3D27D6FC1996EDAE7CF3E1B32B071343B30FB5FCEFBC594C94ED2` |

The review used only HEAD/hash checks and source reads for the six assigned
files plus storage status. It did not run tests, read data or model contents,
open heldout data, perform inference/training, make network/provider calls, or
spend.

## Local verifier check and test-run limitation

The focused pytest command could not start because the system Python 3.13 and
the repository Python 3.11 virtual environment both lack `pytest`. No package
was installed. A no-bytecode direct check of the fit-identity verifier passed:
one exact fit-03 receipt was accepted, and five deliberately changed trainer,
snapshot, target-list, fit-mode, and optimizer-step cases were rejected. This
does not substitute for running the pytest module.

`git diff --check` passed before this iteration was written. The source files
reviewed above were not modified after the PASS; this iteration and the goal
status note are documentation-only additions after that review.

## Current gates

1. Fit 03 remains blocked. Its last observed free-RAM sample was 17%, below
   the 25% start requirement. Do not stop unrelated applications to raise it.
2. When the resource gate is met, perform fresh storage and destination-space
   admission with a unique 1,500,000,000-byte reservation, then follow the
   exact-hash reviewed fit protocol and maintain 10% RAM/VRAM headroom.
3. After a completed candidate, run the separately reserved development-only
   scorer preflight first. Keep heldout locked until that preflight succeeds.
4. The owner confirmed the existing SubRoute at `http://127.0.0.1:4000`.
   Continue read-only route inspection only. No numeric aggregate USD cap has
   been recorded, no spend guard/receipt path is validated, and no generation
   request was sent. A route confirmation is not a spend cap.
