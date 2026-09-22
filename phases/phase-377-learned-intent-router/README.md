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

## Portable sidecar materialization

The fitted head was exported as a 59,725-byte
`wrench.intent-router-sidecar.v1` artifact. It contains only the seven labels,
the calibration-selected `0.5` confidence threshold, and the 2,048-wide
linear head. The artifact hash is
`ADCDFEC780639CB77948FD44783744EF5D36D9F4C1E074249FAEA5876E4F8AA9`.

The real NVFP4 v103 source was materialized into
`D:\models\_wrench-release-candidate-intent-router-7611ea9` with the sidecar
copied as `wrench-intent-router.pt`. The package passed structural validation,
loaded the sidecar on CPU, accepted a direct `3,999,995`-token raw payload in
`160.783 ms` with the embedded mechanical route and zero model calls, and
passed all six 2M/4M retrieval cases with zero model calls. The package
manifest records `mode=opt_in_shadow_only` and `production_enabled=false`.

This proves portable sidecar distribution and hybrid model-local intake. It
does not yet prove learned-router inference inside the runtime, dense-native
attention quality, or independent 5060Ti execution of this new sidecar.

## Optional runtime safety gate

The sidecar was evaluated as an abstain-only safety gate over the existing
free-generation receipt. The direct-generation baseline was `21/44` outcomes,
`10` verified accepts, and `2` prohibited accepts. With the gate, the same
outputs produced `23/44` outcomes, `8` verified accepts, and `0` prohibited
accepts. Gate embedding median/p95 latency was `147.615/225.423 ms`. Receipt
SHA-256:
`58D72333EF50171FB70C85F6927BC98859CC470F6DB807E267A2E00FEFEE47FA`.

The gate is wired into `WrenchWorker` behind
`WRENCH_INTENT_SAFETY_GATE=1`. It can only replace an accepted generated
proposal with an abstention when the predicted family and generated action do
not agree. It never runs on the deterministic mechanical fast path. A real
Transformers worker smoke loaded the sidecar and emitted
`wrench.intent-safety-gate.v1`; malformed generated output was fail-closed to
`abstain`. Receipt SHA-256:
`7F674CCE87A07FB022F47734942F6BB831A7E7ED1BEC52B0299248532DDF8BD0`.

This is an optional safety improvement, not a claim that the learned model is
already a MiniMax replacement. It remains disabled by default and still needs
package-level 5060Ti verification before promotion.

## Reproducibility boundary

The implementation is `tools/train_intent_router.py`, SHA-256
`3A0B77651D1F344A22C815959C4805BCA9037BF96D2C2B9882939591BF95F7F4`. Its
local syntax check passed and the focused tests are in
`tests/test_intent_router.py`. The external
receipts are intentionally kept outside Git under
`D:\models\wrench-intent-router-shadow-20260921` because they contain local
runtime paths. This phase is evidence for a candidate learned routing design,
not a release claim, native dense 4M claim, or MiniMax parity claim.
