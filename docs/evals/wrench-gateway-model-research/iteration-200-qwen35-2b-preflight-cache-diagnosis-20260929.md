# Iteration 200: Qwen3.5-2B preflight cache-directory diagnosis

Date: 2026-09-29  
Disposition: **FAILED SAFELY before model loading**  
Training steps: **0**; held-out data opened: **no**

## Finding

The Iteration 04 one-step preflight stopped in `verify_model_inventory` with
`RuntimeError: local model file set differs from the pinned inventory`. The
pinned source inventory is internally consistent at 13 files and
4,571,274,023 bytes. A read-only inspection of
`C:\wrench-slm-data\weights\Qwen3.5-2B` found those 13 files plus a
Hugging Face-created `.cache` directory containing download metadata and a
revision tree record. The generic pinned-tree scanner recursively includes
every regular file below the selected root, so the additional `.cache` files
make its actual path set differ from the 13-file source-model inventory.

This is a boundary mismatch between the model-file identity inventory and
the local cache metadata layout, not evidence that a pinned model file is
wrong. The preflight correctly failed closed. No model weights were loaded,
no inference or optimizer step ran, and `model_inventory_sha256` remained
null. Resource telemetry recorded a 26.97% minimum free-RAM fraction and
92.37% minimum free-VRAM fraction. The held-out split was not opened.

## Exact identities and retained evidence

- Model: `Qwen/Qwen3.5-2B`, revision
  `15852e8c16360a2fea060d615a32b45270f8a8fc`.
- Source inventory: `qwen35-2b-local-inventory-iter145.json`, SHA-256
  `ACA8AFED9DA75B0F050B408D270766FD77627F1AF401E240F61C3B47D0DB02F9`.
- Candidate manifest SHA-256:
  `D4917EF337978B93D2220A9888CB4F640EDB63E54C8E49F70F0696B175DD2956`.
- Runner SHA-256:
  `56EB92134CFAD772161A4ED1A5A2E708AA7DE101677D170C0143CB80274449BF`.
- Failed run ID:
  `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-PREFLIGHT-20260929-01`.
- Manifest:
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-04-qwen35-2b-preflight-01\run-manifest.json`.
- Resource log:
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-04-qwen35-2b-preflight-01\resources.jsonl`.

The one-shot run identity is consumed and must not be reused. Its reservation
remains active until its terminal outputs are accounted and the reservation
is released.

## Next gate

Prepare a narrowly scoped scanner fix that still pins the model root and
rejects reparse points, but distinguishes the exact approved model files from
Hugging Face's `.cache` metadata. Specify how metadata files are bounded and
accounted without treating them as model weights. Independently review the
new exact source hashes, then use a fresh one-shot preflight ID and output
path. Do not fit the adapter until the new preflight succeeds, receives its
own storage admission, and the fit-start RAM reserve is at least 25%.

This result does not update the provisional model-size ranking, LoRA utility,
task completion, Frontier token savings, or cost estimates.
