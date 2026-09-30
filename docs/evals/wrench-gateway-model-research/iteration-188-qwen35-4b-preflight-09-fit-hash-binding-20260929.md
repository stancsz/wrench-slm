# Iteration 188: Qwen3.5-4B preflight 09 with corrected fit-hash binding

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Outcome

After the Iteration 187 exact-hash PASS for a one-prompt preflight, the
corrected scorer completed `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-09` with
status `PREFLIGHT_COMPLETED`. Both frozen-base and inactive-LoRA outputs
passed the validator. The receipt now records distinct correct identities:

- `training_manifest_sha256` = fit manifest
  `D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E`.
- `training_protocol_sha256` = pinned training protocol
  `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893`.

The oracle-only projection remained unopened, there were zero provider calls,
and no exact-answer score was computed. The one-row preflight is a schema and
local-runtime gate only.

| Measurement | Frozen base | Inactive LoRA |
|---|---:|---:|
| Denominator | 1 | 1 |
| Schema and bounded decision valid | 1/1 | 1/1 |
| Prompt tokens, local tokenizer | 362 | 362 |
| Completion tokens, local tokenizer | 92 | 73 |
| Generation latency | 39.81 s | 32.31 s |
| Frontier requests | 0 | 0 |

Both arms received the same schema-contract-augmented prompt. The result does
not establish exact task correctness, LoRA benefit, production coding
effectiveness, Frontier-token savings, cost reduction, or all-day reliability.

## Identity and resource evidence

| Sealed artifact or package | SHA-256 |
|---|---|
| Corrected scorer | `A64F4D7A92EFC7CAE3EECBA7BB21A62A566C06867D31EB991CCE4F0BB19A877D` |
| Schema-contract protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| `preflight.json` | `5F2F875404B8531BDA0B9A09C02332DC213E69A4814C9DE1A23426CA3476E9DD` |
| `base-predictions.jsonl` | `B60AE4B7FB9595DF15E93D28F02B78BB25C74E5B97896743BA286FD1400F0733` |
| `lora-predictions.jsonl` | `C7C9F13891A24D118999B23984B738AA968C4CD2AEA2C74CAB25558DB50363B5` |
| `resources.jsonl` | `B92DDD78CC1DCF90640F38F04853A9A655B46676D3166F61AADDB39C5945BAC9` |

Exact training identities recorded in the receipt:

- Fit manifest: `d39a9335fbdd107390f053f2460a34845ce3efe2ea473f73060c6eae85278f0e`
- Training protocol: `4b123714bb3c669a98b4d892bd127d69a10adcdb6763cc4059b66fae128e9893`

The 160.95-second job recorded 92 resource samples without a breach. Minimum
free RAM was 24.59%; minimum free VRAM was 6,121 / 16,311 MiB (37.53%); scratch
peak was zero. The pinned RTX 5060 Ti and local BF16 runtime were used. The
optimized causal-convolution and gated-delta kernels remained unavailable, so
Transformers used slower reference PyTorch kernels.

The unique 500,000,000-byte reservation included all required external roots,
including the Docker WSL model volume and automation directory. Destination
space and aggregate budget passed. The run stopped before this report was
written; release the reservation after accounting for the receipt, prediction
files, resource log, and this report.

## Next gate

Obtain a new independent exact-hash review of the 64-row full-score package
using this corrected scorer and receipt. That review must verify the actual
fit-manifest and training-protocol fields, receipt-to-scorer binding, exact
64-row synthetic dev boundary, prediction sealing before oracle access, and
resource/storage controls. The full score needs its own 1,000,000,000-byte
reservation and fresh >=10% RAM/VRAM admission. Keep the held-out split sealed.
