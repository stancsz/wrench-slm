# Iteration 180: 4B LoRA dev preflight 06

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Outcome

Preflight `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-06` completed one prompt for
the frozen base and inactive LoRA arms, then correctly sealed
`PREFLIGHT_FAILED`. Both arms reached the 96-token output cap and returned
invalid JSON. Their exact prompt and response counts were 235 input / 96 output
tokens each under the local tokenizer, for 662 local tokens total across both
arms. There were zero provider calls. The 64-row dev score was not started, and
the sealed oracle projection was not opened.

| Measurement | Base | LoRA |
|---|---:|---:|
| Exact denominator | 1 | 1 |
| Valid JSON decisions | 0 | 0 |
| Exact oracle decisions | 0 | 0 |
| Prompt tokens, local tokenizer | 235 | 235 |
| Completion tokens, local tokenizer | 96 (cap) | 96 (cap) |
| Generation latency | 42.07 s | 41.86 s |
| Failure | `GENERATION_TOKEN_CAP_REACHED`, `OUTPUT_SCHEMA_INVALID` | same |

This is not a quality comparison: the only sampled row is insufficient, and
both arms failed the required output contract. It is also not a Frontier token
or cost result.

## Runtime and resource evidence

The scorer ran in one persistent foreground execution session. The complete
723-tensor BF16 model loaded directly on the RTX 5060 Ti. The exact package
identities were scorer SHA-256
`2C430A1A1C52D3FA0118ACC2421A5D68CE3C665BA6EE40CE71BF400FA3AF2EE8` and
evaluation protocol SHA-256
`328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6`.
The run used the pinned local Python 3.13.15 / Torch 2.14.0+cu132 /
Transformers 5.17.0 / PEFT 0.21.0 / Accelerate 1.15.0 runtime, model revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, and existing adapter
`051a942cc306d15ff22ad300d6256cc4b8e6335b9c6263b65696353b04938e5c`.

The 96 resource samples recorded no floor breach. Minimum free RAM was 23.85%,
minimum free VRAM was 6,152 / 16,311 MiB (37.72%), scratch peak was zero, and
the sealed preflight elapsed time was 162.79 seconds. These samples show this
exact local inference package fits the host's 10% resource floors during this
short diagnostic. They do not prove sustained smoothness. Transformers logged
that causal convolution and gated-delta kernels fell back to reference PyTorch
implementations, so latency may improve with a compatible optimized runtime.

| Sealed artifact | SHA-256 |
|---|---|
| `preflight.json` | `E7687E538EE86E0ED030442576EC316CC2E2F8EF78BD0E77769F3E912BA7ED57` |
| `failure.json` | `F1245CA453190FF413358D5B85DA06615D8E16BB621D591B98DFDDADA4A4CE30` |
| `base-predictions.jsonl` | `4F4C054D57E29BC72A44D995E29E8BB7F4A035423165BBC007F445C348BEA572` |
| `lora-predictions.jsonl` | `96AEF8E45254103F3E01296B1F1AD3A956FCC0CD3EFD0A976D514D4C564D308B` |
| `resources.jsonl` | `AF1C5099F35844A37B83F44023E4C28F11A2B2E5FDA8373C439C0613658DB47C` |

## Next evaluation change

The frozen prompt already requires exactly one JSON object. The captured base
output spent the capped generation on free-form reasoning; the LoRA output
also began with a `Thinking Process` section. The scorer currently calls
`apply_chat_template` without disabling Qwen3.5 thinking mode. The official
[Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B) says thinking
mode is enabled by default and documents an instruct / non-thinking mode. The
locally pinned tokenizer template itself has an `enable_thinking` branch: when
false it closes an empty think block before generation; otherwise it opens a
think block. This is a strong evaluator-configuration hypothesis, not proof
that it is the only cause of the invalid outputs.

Next, prepare a new hash-bound evaluator/protocol revision that passes
`enable_thinking=False` to the pinned chat template for **both** base and LoRA
arms, preserving the frozen prompts, output cap, parsing rules, and oracle
boundary. Obtain independent exact-hash review, then use fresh resources,
storage admission, a new one-shot job ID, and a new preflight. Do not run the
64-row score unless both new preflight arms complete below the cap with valid
schema. The existing failed outputs and receipt remain immutable.

No tests, training, held-out access, model downloads, route changes,
credentials, provider calls, or spending occurred in this iteration.
