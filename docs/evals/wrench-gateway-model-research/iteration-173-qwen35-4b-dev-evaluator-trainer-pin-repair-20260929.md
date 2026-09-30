# Iteration 173: Qwen3.5-4B dev evaluator trainer pin repair

## Disposition

The first local preflight attempt failed before model or tokenizer loading. The
traceback ended in `load_fit_receipt()` with `RuntimeError: trainer identity
mismatch`. This was an evaluator source defect: its `TRAINER_SHA` constant
omitted one `b`. The current trainer file, frozen fit manifest, and prior
review reports all agree on the correct trainer SHA-256
`1d7ccbb42af72c41066d52a4cb6448d000c07d395657cae475daaa79363b49b5`.

The evaluator constant has been corrected to that exact value. No fit manifest,
adapter, model, protocol, data, or active Wrench state was changed. The
candidate remains inactive. An independent source review of the corrected
evaluator is required before another preflight.

## Failed attempt record

- Job: `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-01` (one-shot; do not reuse)
- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
- Exit: code 1 after about 1.1 seconds; not an external timeout
- Model/tokenizer loaded: no
- Inference, predictions, resource monitor, and provider calls: none
- Sealed predictions: no
- The scorer exited before its normal output directory and failure context
  were initialized. The external supervisor retained stdout/stderr and wrote
  a separate failure receipt rather than treating this as a model result.
- Failure receipt:
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\supervisor-WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-01\failure.json`
  SHA-256 `2fc6367c57afc6f8a2eed318913d06e8b8a0f50446798b8f0e762c5933976602`.
- Captured stderr SHA-256
  `ab128de27250963ca96fa837a4fcca304efd5e71a2209b519a5a4069a96e6267`
  (606 bytes); stdout was empty.

## Identity reconciliation

| Item | SHA-256 | Result |
|---|---|---|
| Trainer file | `1d7ccbb42af72c41066d52a4cb6448d000c07d395657cae475daaa79363b49b5` | Matches fit manifest `runner_sha256` and Iterations 163–166 |
| Fit manifest | `d39a9335fbdd107390f053f2460a34845ce3efe2ea473f73060c6eae85278f0e` | Unchanged; binds the trainer SHA above |
| Training protocol | `4b123714bb3c669a98b4d892bd127d69a10adcdb6763cc4059b66fae128e9893` | Matches existing pin |
| Previous evaluator | `14ec4c0939e8135a14d31a9a93e51de6df01da658e6f42a3369967e94c4c2d05` | Had the one-character SHA typo |
| Corrected evaluator | `5b92e5ec7a325b82c265fb082350ef3664361229b850f70b79f31c75a2d255af` | Pins the exact trainer hash above |
| Evaluation protocol | `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6` | Unchanged |

The corrected scorer source is byte-identical to the prior version except for
the missing `b` in `TRAINER_SHA`. The source still refuses to load the model
until it validates the frozen fit manifest, trainer/protocol, model inventory,
projection identities, and reservation. The successful one-prompt preflight
gate and the separate oracle projection rules are unchanged.

## Next gate

Obtain an independent exact-hash review of Iteration 173's corrected scorer.
If it passes, use a new preflight job ID, fresh storage status and reservation,
at least 5 GiB destination headroom, and fresh 10% RAM/VRAM admission with the
external 900-second hard timeout. A preflight pass still only admits the
64-row synthetic dev diagnostic; it cannot prove engineering quality, API
token reduction, cost savings, or sustained all-day performance.
