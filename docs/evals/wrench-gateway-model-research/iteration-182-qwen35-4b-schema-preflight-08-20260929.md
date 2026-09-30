# Iteration 182: Qwen3.5-4B schema-contract preflight 08

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Outcome

The independently reviewed schema-contract package passed the one-prompt
preflight. The frozen base and inactive LoRA both generated JSON accepted by
the unchanged validator. The scorer sealed predictions before any oracle read;
the oracle-only projection remained unopened. There were zero Frontier calls.
This is a one-row schema and runtime gate only. It is not a quality estimate,
and does not admit any 64-row results until the full-score package is reviewed
and receives its own storage reservation.

| Measurement | Frozen base | Inactive LoRA |
|---|---:|---:|
| Denominator | 1 | 1 |
| Schema and bounded decision valid | 1/1 | 1/1 |
| Prompt tokens, local tokenizer | 362 | 362 |
| Completion tokens, local tokenizer | 92 | 73 |
| Generation latency | 40.09 s | 32.35 s |
| Frontier requests | 0 | 0 |

Both arms saw the identical transformed input (`d5fad0701a58e81ae39cbd920598719de99b9f8f2c748e7b76d41955bfda8043`). It includes the fixed schema contract appended after the prompt projection's source hashes were verified. This raises the prompt from 237 tokens in iteration 181 to 362 tokens under the local tokenizer. That is interface guidance overhead, not token savings. The LoRA selected `LOCAL_COMPACTION` / `COMPACT`, preserved the visible evidence IDs, and emitted an allowed reason code. The base also passed schema validation. No answer labels were opened, so neither output was scored for exact task correctness.

## Runtime and integrity

The exact-hash static review `WRENCH-QWEN35-4B-SCHEMA-CONTRACT-PACKAGE-REVIEW-ITER182-20260929`
(nonce `90f4b09f-46f8-466b-a4f3-cfe91da05a3f`) passed for this one-prompt
preflight only. It noted that the prompt contract does not spell out every
validator detail, such as the exact output-key set and list-of-string type;
the unchanged validator still enforces those constraints and failed closed.

| Identity or receipt | SHA-256 |
|---|---|
| Evaluator source | `86040E775FE5EC60B9C018BA3BD0DA82F07A14C24C972A754720C0B0CCB8AABF` |
| Schema-contract protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| `preflight.json` | `71F4F188D6D45D48F338ED0F301A6B8A6C8103BE564B9F0BC7EBDB59B31242E2` |
| `base-predictions.jsonl` | `7854C5937276B3F212C4DD135F9972F30907120C7F4A3062C9A185CB877CBE9C` |
| `lora-predictions.jsonl` | `7CDAF6ED1E507836B02F64A4ED27F23B0D6D0DC4E6FF71CA280D538709EF81E0` |
| `resources.jsonl` | `BDB3D81FCDC5C85EC1B1B37774ACB4B5E85B59D8E41E3432951F62D5C0A05707` |

The job completed in 155.73 seconds using the pinned Qwen3.5-4B revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, the installed inactive adapter,
and the pinned local runtime on the RTX 5060 Ti. Eighty-nine resource samples
recorded no breach: minimum free RAM was 24.11%, minimum free VRAM was 6,148 /
16,311 MiB (37.69%), and scratch peaked at zero bytes. Optimized causal-conv
and gated-delta kernels were unavailable, so Transformers used slower
reference PyTorch kernels.

The 500,000,000-byte reservation was admitted with all required roots, including
the Docker WSL model volume and automation directory. C: had 130.7 GB free at
admission. The run produced only the bounded prediction, receipt, and resource
files; its reservation is released after those outputs are accounted.

## Interpretation and next gate

This preflight does not establish LoRA advantage, model quality, 95/5 routing,
Frontier token reduction, provider cost, or all-day coding reliability. The
362 local prompt tokens and 92 / 73 local completion tokens are not provider
usage measurements. The next admissible experiment is the separately reviewed
64-row synthetic development score, with its own storage admission. Preserve
the sealed held-out split and do not use this one-row result as evidence of
product effectiveness.
