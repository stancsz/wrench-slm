# Iteration 197: Qwen3.5-4B LoRA synthetic dev score

Date: 2026-09-29  
Assignment: `WRENCH-QWEN35-4B-DEV-SCORE-20260929-03`  
Independent review: `WRENCH-QWEN35-4B-DEV-SCORE-REVIEW-20260929-01`, nonce
`338ab09b-0ff2-4f31-977f-75e7c1c6a173`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Status: **synthetic dev diagnostic completed and independently reconstructed; no product acceptance claim passes**

## Question

Does the pinned Qwen3.5-4B base plus its Wrench-specific LoRA learn the
bounded evidence-selection, compaction, route, and retrieve-stop decisions
needed by the gateway, and did the exact model fit the available host safely?

## Paired results

The scorer ran the base and adapter on the same 64 prompt-only synthetic dev
rows, then compared predictions against the sealed-after-prediction dev oracle
projection. The independent reviewer re-counted the 64 paired decisions and
confirmed all assigned output and source identities.

| Measure | Base | Wrench LoRA |
|---|---:|---:|
| Exact five-field decision | 18/64 (28.125%; Wilson 95% CI 18.6%-40.1%) | 26/64 (40.625%; Wilson 95% CI 29.5%-52.9%) |
| Compaction policy | 2/16 | 10/16 |
| Evidence selection | 16/16 | 16/16 |
| Route family exact decision | 0/16 | 0/16 |
| Retrieve-stop family exact decision | 0/16 | 0/16 |
| Valid output schemas | 64/64 | 59/64 |
| Route field correct across all rows | 55/64 | 48/64 |
| Authority violations / invalid evidence references | 0 / 0 | 0 / 0 |

The paired delta is +8/64, or +12.5 percentage points, driven by compaction.
The adapter regressed schema validity by five rows and route-field accuracy by
seven rows. Neither arm correctly solved the route or retrieve-stop families.
The gain therefore supports a narrow compaction follow-up, not routing
authority or an all-purpose gateway controller.

## Hardware and exact identities

The run used `Qwen/Qwen3.5-4B`, revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, on the RTX 5060 Ti with 16,311 MiB
VRAM. Across 2,908 resource samples, minimum free RAM was 22.60%; minimum free
VRAM was 6,043 MiB (37.05%). The 10% floor was never breached and peak Wrench
scratch was zero. This proves that this bounded BF16 scoring run fit safely; it
does not prove sustained all-day runtime, good latency, training on other
machines, or representative coding work.

| Artifact | SHA-256 |
|---|---|
| `result.json` | `A3703865D622037E266BCBB1655FF4536B85CC1410142A1686F22D1BBFF395BA` |
| `base-predictions.jsonl` | `23C8A1B67F8C21F4D94CC39A8C19E209612D576A2338EAD26F3A426CE838B705` |
| `lora-predictions.jsonl` | `B6CE379BD101599C005B84AC1604828D8A5FF318AF07631195AA2F8E85B5DFDA` |
| Resource log | `A9292568E80D621A3CF56D05A127310D0558680938D2130B0CB92DADCF134BAF7` |
| Adapter | `051a942cc306d15ff22ad300d6256cc4b8e6335b9c6263b65696353b04938e5c` |
| Model inventory | `30b09cf32f06fae5418a0b925820202bfddf9e1c2a1f009d12e6396d10aed15a` |
| Prompt projection | `6be3c1e65342711af8fcb7c6f44ed53b5986d31ad93fe0c9ee1542e537268baf` |
| Dev oracle projection | `b6ac5d5c81a1390cc8a9a12d065e8c58cd62242a3308c754641424b1cf783701` |

The run wrote 141,171 bytes across the three score outputs. The 1,000,000,000
byte score reservation was released after the process exited and outputs were
counted. The independent review wrote no files; its 5,000,000 byte reservation
was then released.

## Model-size decision effect

This result raises confidence that 4B plus LoRA can improve this synthetic
compaction-policy slice, but it does **not** establish that 4B is the best
gateway size. Previous same-runner evidence found that 4B preserved all three
answers under the aggressive related-table context arm while 2B preserved
2/3, but it used only three reused development tasks. On that battery, 4B
took 101.23 seconds versus 67.40 seconds for 2B. The answer-blind related-path
arm passed 3/3 for both; its target-tokenizer component reduction was 94.32%,
and the aggressive table arm's was 94.94% for 4B. Neither is Frontier API
usage.

Qwen3.5-2B remains the provisional overall small-gateway lead because it has
the stronger task-matched external LoRA evidence and lower on-host latency and
memory in the existing three-case comparison. Qwen3.5-4B remains the
high-priority compaction challenger because it passed the aggressive table
cases and its new LoRA improved compaction. Confidence is low: there is no
same-64-row 2B LoRA arm, the 4B LoRA has serious route/schema failures, and
neither model has representative coding-work or all-day evidence. Keep the 4B
adapter inactive. The next informative size comparison is a reviewed 2B LoRA
fit scored on this same dev projection, then a broader frozen coding battery
before candidate selection.

## What this does not prove

- The data are synthetic and the result is a development diagnostic, not a
  fresh holdout or real coding-episode evaluation.
- No held-out payload was opened.
- No Frontier call occurred. The recorded tokenizer values are local; Frontier
  input/output token savings, provider cost, and all-in cost remain unmeasured.
- There is no proof of 95% locally completed tasks, at most 5% Frontier
  routing, 95% success retention, 95% Frontier-token savings, or all-day
  engineering reliability.
- The 64-row semantic score is not directly comparable to the three-task
  source-retrieval battery or external benchmark tables.
