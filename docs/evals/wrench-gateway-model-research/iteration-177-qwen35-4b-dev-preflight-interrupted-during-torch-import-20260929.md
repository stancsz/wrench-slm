# Iteration 177: Qwen3.5-4B preflight interrupted during Torch import

## Result

The third one-shot preflight passed the fit, trainer, model inventory/config,
prompt-only projection, and all reviewed local identity checks. It reached
`prepare_model()` and began importing the pinned Torch package. The Python
process then received a control-C style interruption while loading Torch DLLs.
Windows reported process exit code `-1073741510` (`0xC000013A`); Python
recorded `KeyboardInterrupt`.

The cause of that interrupt is unknown. It was not the 900-second supervisor
timeout, a recorded RAM/VRAM floor breach, or a scorer validation failure. Do
not treat the attempt as a pass or as a model failure. No tokenizer/model
weights were loaded, no inference ran, no predictions were sealed, and no
provider/SubRoute call occurred. The LoRA remains inactive.

## Pinned identity and run accounting

- Job ID: `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-03` (one-shot; do not reuse)
- HEAD: `af01304824f079a64b6c3902397a2034b843511a`
- Corrected scorer SHA-256:
  `9e60927ae12d196f5cbe2c9c1f37e64c3ff3f2ca885b09eb7029ba75c5094b9e`
- Evaluation protocol SHA-256:
  `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6`
- Elapsed: about 66.7 seconds; exit status `-1073741510`; supervisor stop reason
  was empty because the scorer exited before the external timeout.
- Failure receipt:
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-eval\preflight-WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-03\failure.json`
  SHA-256 `43a15495af84ba4a05a0ae1c9f477eb2fe4117fd50be3d6e0f000c48ae41fa84`.
- Resource log:
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-eval\preflight-WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-03\resources.jsonl`
  SHA-256 `feb7f971d1178ac4984b60de90f1f397a42e672f27121ffd926a82278de21325`
  (2,123 bytes; six setup/import samples).
- Supervisor stderr SHA-256
  `2aa6a4915393a204d54e22168cb35f6c02bbddb800d1a66b8fc3985f1f72ac35`
  (984 bytes); stdout was empty.

Recorded free RAM ranged from 23.99% to 24.63%; GPU free memory ranged from
15,190 to 15,211 MiB of 16,311 MiB. The 10% floors held in all six scorer
samples and the external supervisor samples. Runtime scratch remained 0.
The final sample was about 24.5% free RAM and 15,198 MiB free VRAM. No Wrench
inference process remained after the exit.

## Next operational step

The current supervisor was attached to the calling shell session, and this
attempt ended with an unexplained control-C style status. Before a new
one-shot attempt, use a detached supervisor process that records its own PID,
child PID, start/heartbeat/exit status, enforces the same 900-second hard
timeout and 10% resource floors, caps redirected logs at 20 MiB, and writes a
failure receipt if it stops the scorer. Use a fresh job ID and reservation.
Do not change the scored package or inference inputs to work around an
interruption. A passing one-prompt preflight still only admits the synthetic
64-row dev diagnostic, not a claim about coding effectiveness or token/cost
savings.
