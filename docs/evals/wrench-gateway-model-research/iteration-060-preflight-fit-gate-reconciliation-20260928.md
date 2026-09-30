# Iteration 060: reconcile preflight evidence and the fit-package gate

## Current host admission

The hourly recheck measured 3,165.3 / 32,701.8 MiB free RAM (9.68%),
15,225 / 16,311 MiB free VRAM on the RTX 5060 Ti, and 141.04 GB free on C:.
The process query found no Wrench training, inference, or benchmark process.
Fit 03 requires at least 25% free RAM at start and 10% RAM/VRAM throughout.
No model runtime, test, training, benchmark, or provider request was started.

The GPU has ample idle VRAM, but current RAM is below even the 10% floor and
well below the fit start requirement. The prepared experiment remains the
Qwen3.5-0.8B attention-only LoRA fit, with a 1,500,000,000-byte reservation
and at least 5 GiB of destination headroom required immediately before fit.

## Verify the existing preflight instead of repeating it

Read the preflight-05 `run-manifest.json` and `resources.jsonl` under the
approved Wrench data root and recomputed hashes for the manifest, resource
log, trainer, scorer, protocol, and iteration records. The manifest reports
`PREFLIGHT_COMPLETED`, with one optimizer step over eight synthetic train
rows, 24 `self_attn` q/k/v/o targets, and 540,672 trainable parameters. It has
`output_dir: null`, `fit_mode: false`, and
`heldout_opened_by_runner: false`. The recorded resource minima were 10.9850%
free RAM and 54.4663% free VRAM.

The manifest runner hash matches the current trainer:

`62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC`

The manifest protocol hash matches the current protocol:

`EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A6E75EE12DACE33B5`

Other verified identities:

| Artifact | SHA-256 |
|---|---|
| Scorer | `0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5` |
| Iteration 008 | `0963C837079CDC76F3D5A34BE7FF01C5BE888C720611D96704E6AD3AB69CD8C3` |
| Iteration 009 | `F9BE4ED927D62E691A2C5DF97A50AEA3CA502BBE2524A5E47F68009A01BDFCE5` |
| Preflight manifest | `D5DC3E8F896FCA8A4BF23BA2E0E224EA4482A2E6074EB2FAD65EB6572B018131` |
| Preflight resource log | `A6E5B76B729C6988DE5D3ACC132442D1F317D77B40E3E1BFB34F9BD28F0693F1` |

The protocol's closing sentence still says preflight 05 has not run. It is
stale against the completed manifest and Iteration 008 receipt. The protocol
is hash-bound, so it was not edited. Do not repeat preflight 05 unless its
trainer, protocol, data, model, or runtime identity changes.

## Fit-package review reconciliation

The current GOAL header previously stated that fit-package review 05 passed.
However, the review artifact was not found under the current `docs/evals` or
`docs/reports` trees, and Iteration 008 says the updated goal and iteration
record need a fresh exact-hash package review before fit 03. The independent
Iteration 009 scorer-binding review covers trainer, scorer, and protocol
hashes, but not the current goal and Iteration 008 package scope. Treat review
05 as unverified until its receipt is located or a fresh independent review
records the full current scope. The GOAL status line now reflects this.

## Hourly job and next action

Updated the existing `wrench-hourly-token-reduction-monitor`; it remains
ACTIVE, hourly, and attached to this thread. It now reuses the verified
preflight receipt, resolves the package-review gap once, and launches fit 03
when the review, live RAM/VRAM, fresh storage reservation, disk headroom, and
other exact gates pass. The owner already directed the bounded local
experiment to proceed once the hardware can run it, so the hourly job does not
wait for another approval. Paid SubRoute generation remains separate and
closed without its numeric campaign cap and shared caller ledger.

Storage status was `WITHIN_LIMIT` at 10,993,249,229 bytes actual and
8,103,000 bytes in active reservations. This report/goal update reserved
100,000 bytes under
`WRENCH-PREFLIGHT-FIT-GATE-RECONCILIATION-20260928-01`; release it after final
accounting. No Luna consultation or delegated job was used because the host
was below the resource floor and the next experiment gate is explicit in the
protocol.

The preflight is compatibility evidence only. The adapter, decision quality,
coding ability, 95/5 success mix, 95% frontier-token reduction, 95% all-in
cost reduction, and all-day engineering remain unproven.
