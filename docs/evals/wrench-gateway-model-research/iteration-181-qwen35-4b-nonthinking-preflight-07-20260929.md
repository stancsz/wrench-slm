# Iteration 181: Qwen3.5-4B non-thinking preflight 07

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Review and outcome

The exact-hash static review `WRENCH-QWEN35-4B-NONTHINKING-EVAL-PACKAGE-REVIEW-ITER181-20260929`
(nonce `d528a191-4b2a-4d57-91d3-879c3e42ca66`) passed for the one-prompt
preflight package after a mistaken path finding was corrected. The reviewer
confirmed `enable_thinking=False` reaches both arms, the local tokenizer
template supports it, the frozen prompts and schema checks remain, predictions
are sealed before oracle access, and no provider path was added. This review
does not admit full scoring.

Preflight `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-07` ran both frozen arms on
the same first dev prompt. It sealed `PREFLIGHT_FAILED` because both responses
were valid JSON but violated the scorer's closed enums. The 64-row score did
not start; the oracle projection remained unopened; there were zero provider
calls.

| Measurement | Base | LoRA |
|---|---:|---:|
| Denominator | 1 | 1 |
| Valid schema | 0/1 | 0/1 |
| Exact oracle decision | 0/1 | 0/1 |
| Prompt tokens, local tokenizer | 237 | 237 |
| Completion tokens, local tokenizer | 91 | 70 |
| Generation latency | 39.46 s | 30.02 s |
| Validation failures | `ROUTE_ENUM`, `OPERATION_ENUM`, `REASON_ENUM` | `REASON_ENUM` |

This is not a quality estimate. On the one sampled row, the LoRA output chose
the expected `LOCAL_COMPACTION` route, `COMPACT` operation, and the three
visible hot evidence IDs, while its `reason_code` was outside the allowed enum.
The base output also used an evidence ID as its route and chose an unsupported
operation. This one-row observation is a useful diagnostic, not a product
claim or evidence that the LoRA generalizes.

## Runtime evidence

The reviewed scorer SHA-256 was
`9C36B221E15B17BBECD310BFAD1AA7EE7E6A1CF8526C93B1493B2461F79AD31C`; proposed
protocol SHA-256 was
`9BF69AE4668803F1BB1C170944281832D272C8CEA0D8F0FE96411C5175E2AE7F`. Model,
adapter, tokenizer, data, runtime and GPU identities remained those recorded
in the screen-03 protocol. The persistent foreground job completed in 159.48
seconds. Ninety resource samples recorded no breach; minimum free RAM was
23.31%, and minimum free VRAM was 6,166 / 16,311 MiB (37.80%). The reference
PyTorch fallbacks for causal convolution and gated-delta operations remained
in effect.

| Sealed artifact | SHA-256 |
|---|---|
| `preflight.json` | `0B831B2226DE0857AABC7427007C5E1FBB09E3E3B2EBB23C95949DE40C223BA6` |
| `failure.json` | `9DC89145AB179A1F7836FAE195CD26E41E76C3A6B01820457A0F7328C198C547` |
| `base-predictions.jsonl` | `88F3FB485B1A867BB655FAABA68B2EFC064EBC27D6AB09F38E0C929D5FB8E389` |
| `lora-predictions.jsonl` | `59A11C67942FC1302D9EEAA4CED08166FCBABDAF7953AB6ECF3D10FFC3FBBFFD` |
| `resources.jsonl` | `2CA8AFA9240216C70235C2095E4B5726878B5F60C5A1A217163E5CAFF547A93E` |

## Next step

The frozen system message names the JSON fields but does not give the allowed
route, operation, or reason-code enum values. The grader enforces those values,
so the local controller is being asked to choose among hidden labels. A
deterministic schema contract should be part of the model-visible Wrench
request. The next dev-only revision will add the exact permitted enum lists to
the system context for both base and LoRA arms while keeping task messages,
labels, scorer, and 96-token generation cap fixed. This exposes interface
requirements, not the expected per-example answer. Treat it as development
tuning on the dev split; preserve the held-out split and report this change
explicitly. Obtain exact-hash review and fresh one-shot preflight admission
before inference. Full scoring remains closed until that preflight passes.

This run shows the 4B package remained inside host resource floors for a short
diagnostic; it does not establish smooth all-day inference. Local tokenizer
counts are not Frontier usage or savings. No tests, training, held-out access,
provider calls, route changes, credential reads, or spending occurred.
