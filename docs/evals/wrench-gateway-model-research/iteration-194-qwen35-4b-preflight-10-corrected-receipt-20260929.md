# Iteration 194: Qwen3.5-4B preflight 10 with corrected manifest bindings

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Outcome

The Iteration 193 static review passed the exact scorer package for a fresh
one-prompt preflight. Run
`WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-10` completed with
`PREFLIGHT_COMPLETED`; the base and inactive LoRA each passed the bounded
output validator. The receipt now binds distinct, correct evaluator,
evaluation-protocol, fit-manifest, training-protocol, prompt-manifest, and
prompt-payload hashes. The oracle-only projection remained unopened, and
there were zero provider calls. Exact task correctness was not scored.

| Measurement | Frozen base | Inactive LoRA |
|---|---:|---:|
| Denominator | 1 | 1 |
| Schema and bounded decision valid | 1/1 | 1/1 |
| Prompt tokens, local tokenizer | 362 | 362 |
| Completion tokens, local tokenizer | 92 | 73 |
| Generation latency | 43.14 s | 31.31 s |
| Frontier requests | 0 | 0 |

## Receipt binding

| Receipt field | Value | Expected pin | Match |
|---|---|---|---|
| `evaluator_sha256` | `4E2E69E1AE89B553470FE3ABE9EE5776C70D35942B99E8B4509C7FA71F159E85` | Current reviewed scorer | Yes |
| `evaluation_protocol_sha256` | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` | Current schema-contract protocol | Yes |
| `training_manifest_sha256` | `D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E` | Fit manifest | Yes |
| `training_protocol_sha256` | `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893` | Training protocol | Yes |
| `prompt_manifest_sha256` | `DC4C3B605F7CC2AC62AA283BDD90B55FBCDA7CB4BF526441306EC25508167939` | Prompt manifest file | Yes |
| `prompt_projection_sha256` | `6BE3C1E65342711AF8FCB7B6CF44ED53B5986D31AD93FE0C9EE1542E537268BAF` | Prompt-only payload | Yes |

## Artifacts and runtime

| Sealed artifact | SHA-256 |
|---|---|
| `preflight.json` | `2EE25973921278FFE5491A5DD105F95A8F0219EC84943FFBEB577E268B1909C1` |
| `base-predictions.jsonl` | `462C2BD0B6900C8D76983C581930C64947F3B5AF27C3A39B48424A47C7A69720` |
| `lora-predictions.jsonl` | `F4A04A9A56F62FCBFB84B03342AA624CCCA4149D0579674D380CEE964CFCE9E9` |
| `resources.jsonl` | `D54809BC08600F5FAD93CFA3D5D2820AFA39EDD9366437E2C7ADBFADCE8F4D75` |
| Scorer source | `4E2E69E1AE89B553470FE3ABE9EE5776C70D35942B99E8B4509C7FA71F159E85` |
| Iteration 193 static preflight review | `67E88567942969DA87784DA2BA7798FDE804D18F135BEFD8320B85D4DACE6475` |

The 163.90-second run recorded 94 resource samples without a breach. Minimum
free RAM was 23.87%; minimum free VRAM was 6,112 / 16,311 MiB (37.47%); scratch
peak was zero. The pinned Qwen3.5-4B revision, inactive adapter, runtime, and
RTX 5060 Ti were used. Optimized causal-convolution and gated-delta kernels
were unavailable, so Transformers used slower reference PyTorch kernels.

The job used a unique 500,000,000-byte reservation with the Docker WSL model
volume and automation directory included. The reservation remains active until
the prediction files, receipt, resource log, and this report are accounted and
released.

## Interpretation and next gate

This successful one-row diagnostic does not prove task quality, LoRA benefit,
95/5 routing, Frontier-token reduction, provider cost, all-in cost, or all-day
engineering. Local tokenizer counts are not Frontier usage. Obtain a fresh
exact-hash review of the full-score package with this scorer and receipt. Only
after it passes may a 64-row synthetic development score start under a
separate 1,000,000,000-byte reservation, >=5 GiB destination headroom, and
fresh >=10% RAM/VRAM admission. Preserve the held-out split.
