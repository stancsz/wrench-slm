# Iteration 175: Qwen3.5-4B prompt helper pin repair

## Disposition

Preflight job `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-02` failed while
checking the prompt-only projection manifest. It exited before reading the
prompt payload and before loading tokenizer/model runtime packages. No
inference or provider call occurred; the adapter remains inactive.

The projection helper, generated prompt manifest, and Iteration 169 receipt
all bind helper SHA-256
`92e90f2f323bac9f917c06de318fa3b4e89ec0fd5fc7dc00989e2a7ef3ed88b8`.
The scorer's previous `PREP_HELPER_SHA` literal was only 63 hex characters,
missing one `9`. The source now carries the full 64-character digest. The
Iteration 173 trainer-pin correction remains in place. No model, adapter,
training receipt, prompt/oracle projection, protocol, or held-out data changed.

The read-only reconciliation compared all source/manifest identities loaded
before model preparation: trainer, training protocol, fit manifest, fit
resource log, fit epoch metrics, model inventory/config, pinned-tree helper,
prompt helper, prompt projection/manifest, and all three adapter files. These
digests matched their pins after the repair. The prompt manifest's helper hash
matched both the current helper file and the corrected source pin. The
diagnostic did not open the oracle projection or any held-out path.

## Failed attempt evidence

- Job ID is one-shot and must not be reused.
- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`.
- Process exit code: 1 after about 39 seconds; no external timeout.
- Prompt projection manifest was read and its pinned SHA checked. Its fields
  were compared before the prompt-only payload was opened.
- No prompt payload, oracle manifest/payload, held-out payload, tokenizer,
  model, or inference was loaded.
- Scorer failure receipt:
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-eval\preflight-WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-02\failure.json`
  SHA-256 `97a9ec1967bf890dab84a526914c06f2b32298dc07f22ad525877b7e2ed69654`.
- Resource samples:
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-eval\preflight-WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-02\resources.jsonl`
  SHA-256 `da0f66a4dca834b677e14c6af67c910b161bebfc9e1ed6c4c67e9a40b5d1e2fc`
  (708 bytes; setup-time only).
- Supervisor stderr SHA-256
  `a55656c8ea6476404cfa9c50892d8eabdba625fdea5bea76ff1c021d180d2502`
  (741 bytes); stdout was empty.

## Current repaired identity

- Trainer pin correction remains part of the scorer.
- `PREP_HELPER_SHA` is now the verified 64-character helper digest above.
- Corrected scorer SHA-256:
  `9e60927ae12d196f5cbe2c9c1f37e64c3ff3f2ca885b09eb7029ba75c5094b9e`.
- Evaluation protocol remains SHA-256
  `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6`.
- Prompt-only projection and manifest retain their original pinned hashes.

The next step is an independent exact-hash source review that compares every
pre-model input pin to its current artifact identity. If it passes, only then
may a new one-shot preflight be considered, with fresh storage and RAM/VRAM
admission and the external hard timeout. Even a passing preflight and 64-row
synthetic dev score would not prove production task success, Frontier token or
cost savings, or sustained engineering performance.
