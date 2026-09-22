# Phase 377: learned intent router shadow

Status: `SHADOW_CANDIDATE_PASS`, not production enabled.

This phase implements the smallest learned intervention suggested by the Sol
advisor after the repeated free-form generation gap: a frozen Qwen embedding
plus a small linear head that selects one of the six allowlisted tool families
or `abstain`. It never generates JSON. A selected family still goes through
the existing deterministic mechanical route and the independent verifier.

The advisor decision changed the next experiment, so
`decision_changed=true`. Provider usage was `codex-sol-advisor`, 467 prompt
tokens, 603 completion tokens, 1,070 total tokens. The compact packet was
used only for design advice. It did not write code or execute a command.

## Development result

Command, using only the calibration split for training and threshold
selection:

```powershell
D:\models\wrench-transformers517-py311\Scripts\python.exe tools/train_intent_router.py `
  --model D:\models\wrench-v2-head-only-r16-20260921 `
  --calibration evals\wrench-expanded-v2\calibration.jsonl `
  --development evals\wrench-expanded-v2\development.jsonl `
  --allowed-root . `
  --output D:\models\wrench-intent-router-shadow-20260921\development-receipt-batch1.json `
  --batch-size 1 --fit-steps 300 --cv-folds 5
```

The receipt reports:

- `41/44` outcome matches and `23/44` exact target objects.
- `21/44` verified accepts, `0` prohibited accepts, and `23` abstentions.
- Embedding median/p95 latency `143.467/168.259 ms` on `cuda`.
- Five-fold calibration selected confidence threshold `0.5` and found a
  zero-prohibited threshold during calibration-only cross-validation.
- Receipt SHA-256:
  `9E6C71CE0A9FA4E9B6EE60E9CA997A17DE1DF54C1F2A5681A4422EB1D1EDC8DC`

## Sealed-final diagnostic

The final split was evaluated once, with an explicit
`--allow-sealed-final` guard. It was not read during training, threshold
selection, or any code decision. The receipt reports:

- `42/44` outcome matches and `24/44` exact target objects.
- `22/44` verified accepts, `0` prohibited accepts, and `22` abstentions.
- Embedding median/p95 latency `142.498/170.087 ms` on `cuda`.
- The only two mismatches were expected health reads rejected by the absent
  local health fixture. There were no prohibited accepts.
- Receipt SHA-256:
  `533C196EA28481022FF97B4223A2393E5ED8DFCBDDD105CEF199BB2FB7D89D86`

The experiment clears the advisor stop conditions: more than `10/44`
verified accepts, zero prohibited accepts, and p95 below one second. It is
still not promoted because the dataset manifest is marked
`DRAFT_PENDING_HUMAN_APPROVAL`, the health cases need a real allowlisted
fixture, and the router has not yet been packaged or independently verified
on the 5060Ti. The deterministic hybrid worker remains authoritative.

## Reproducibility boundary

The implementation is `tools/train_intent_router.py`, SHA-256
`3A0B77651D1F344A22C815959C4805BCA9037BF96D2C2B9882939591BF95F7F4`. Its
local syntax check passed and the focused tests are in
`tests/test_intent_router.py`. The external
receipts are intentionally kept outside Git under
`D:\models\wrench-intent-router-shadow-20260921` because they contain local
runtime paths. This phase is evidence for a candidate learned routing design,
not a release claim, native dense 4M claim, or MiniMax parity claim.
