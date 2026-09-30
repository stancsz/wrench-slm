# Iteration 146: same-harness 0.8B versus 2B comparison

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-LOCAL-CONTEXT-ITER146-QWEN35-08B` and `WRENCH-QWEN35-2B-SNAPSHOT-DOWNLOAD-ITER145`  
Status: **Qwen3.5-2B ran in BF16 on the host and matched 3/3 Wrench-context answers; the 0.8B control also matched 3/3. Both crossed 95% local-model token reduction on this tiny synthetic fixture, while target-tokenizer prompt reduction remained about 92%.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question

Does the leading Qwen3.5-2B controller candidate load and run on the RTX 5060
Ti, and does it improve the same Wrench-prepared task results over the 0.8B
control under the same prompt, context budget, fixture, and verifier?

## Model admission and source changes

The pinned 2B snapshot is Qwen/Qwen3.5-2B revision
`15852e8c16360a2fea060d615a32b45270f8a8fc`, Apache-2.0. Its 13 upstream
files total 4,571,274,023 bytes. The weight shard and tokenizer matched their
upstream LFS SHA-256 values; the other files matched their pinned Git blob
IDs and sizes. The local inventory verifier returned
`VERIFIED_LOCAL_SNAPSHOT` for all 13 files. No model code was trusted or run
from the repository (`trust_remote_code=False`).

The snapshot verifier now accepts a model directory below the approved
weights root and a candidate manifest containing a full pinned commit. It
checks the exact file set, per-file sizes, Git blob IDs or upstream LFS
SHA-256, total byte count, and writes an inventory only below the approved
artifact root. The paired runner accepts explicit model identity and local
inventory paths through `WRENCH_DEMO_MODEL_*` variables; its default remains
the prior 0.8B identity. These bindings enabled both sizes to use one runner.

## Paired results

Both runs used the same source revision, three authored synthetic lookup
cases, 64-token Wrench context budget, deterministic decoder, and exact-answer
verifier. Each model answered both a full-fixture arm and a Wrench E0 arm.
The target counts use the pinned MiniMax M3 tokenizer; the local counts use
the tested model tokenizer. “Token reduction” below is only the paired prompt
mechanics result against the synthetic full-fixture input.

| Measure | Qwen3.5-0.8B BF16 | Qwen3.5-2B BF16 |
|---|---:|---:|
| Full-context answers verified | 2/3 | **3/3** |
| Wrench E0 answers verified | 3/3 | 3/3 |
| Local-model input tokens, full → Wrench | 26,196 → 1,248 | 26,196 → **1,238** |
| Local-model input reduction | 95.235914% | **95.274088%** |
| Local-model input + output tokens, full → Wrench | 26,226 → 1,274 | 26,221 → **1,263** |
| Local-model total-token reduction | 95.142225% | **95.183250%** |
| Target-tokenizer prompt tokens, full → Wrench | 19,297 → 1,534 | 19,297 → **1,521** |
| Target-tokenizer prompt reduction | 92.050578% | **92.117946%** |
| Model load / total runtime | 6.2816 s / 46.3153 s | 13.1012 s / 52.0125 s |
| Peak CUDA allocated / reserved | 2.678 / 2.894 GB | 4.991 / 5.249 GB |
| Minimum free RAM, outer guard | 13.74% | 12.13% |
| Minimum free VRAM, outer guard | 75.13% | 61.23% |

Both runs completed with 0 frontier calls and $0 provider spend. The outer
watchdog sampled every 0.5 seconds and stopped only the launched model process
on a resource-floor or telemetry failure. Neither run breached the 10% RAM or
VRAM floor. The 2B run completed while still leaving at least 12.13% sampled
system RAM and 61.23% VRAM free. Transformers used reference fallbacks because
`causal_conv1d` and `flash-linear-attention` were absent; the measured 2B total
runtime was 52.0 seconds for six short generations.

## Decision

For the next **trained bounded controller** experiment, advance Qwen3.5-2B and
retain 0.8B as the control. This same-harness sample gives 2B a small
advantage: one more full-context answer passed, Wrench-context answers were
equal, local prompt reduction improved by 0.038 percentage points, and the
target-tokenizer prompt fell by 13 tokens. The tradeoff was a 5.7-second
longer total run and about 2.36 GB more peak CUDA reservation. The direct
results are consistent with, but much weaker than, the external task-specific
LoRA evidence for 2B.

This is only a three-case synthetic lookup comparison. It cannot establish a
general model-size winner, a coding-success rate, 95% local task coverage,
5% routing, frontier-only success retention, all-day engineering, or a trained
Wrench LoRA benefit. The 95.27% figure is **local-model input reduction on
this fixture**, not the product's 95% frontier-token-saving proof. The
target-tokenizer reduction is 92.12%, and full-lifecycle frontier-token
savings remain unmeasured.

## Identities

| Artifact | Size | SHA-256 |
|---|---:|---|
| 2B candidate manifest `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\qwen35-2b-candidate-manifest-iter145.json` | 2,665 bytes | `D4917EF337978B93D2220A9888CB4F640EDB63E54C8E49F70F0696B175DD2956` |
| 2B verified local inventory | 3,285 bytes | `23E0D5F79E57D41AB9F007B697D8F75F56F5F528519BFDF15F406E1F28DF3DD5` |
| 2B snapshot receipt | 660 bytes | `59D1D57DFD5A4CA4C525C926BD507B11634969EC7E473D4378649203C2120014` |
| 2B paired receipt (Iteration 145) | 6,154 bytes | `9DD6FD0BCDE1C1A030EE231B5FEC14203B579EEA24C372D8A1D11C2BE7FDF403` |
| 2B outer resource-guard log | 20,821 bytes | `351A942CECE195D55EE25C1E520C67E35EF4CBB1ECF627927FE6BEA035E109DA` |
| 0.8B paired receipt (Iteration 146) | 6,171 bytes | `773602FEC7E14EF75378A55A309C299926308E619A3C10A4360EE3F01F8FA764` |
| 0.8B outer resource-guard log | 18,764 bytes | `9C46460832A4BE8DC09E287DA6F11A4309ADFCC856AB95D94A42A8573D462150` |
| Paired runner | — | `ED6FEF1B70D7F879C1969D110E0A74AD3A52D559DFF90A04A30D518C7765BE05` |
| Snapshot verifier | — | `E6F568CAD5807ED66F41203F2175DF5AF47B3E507DB94FE7B1C44787B95BB494` |

The 2B and 0.8B receipts each bind the tested repository revision, fixture,
model revision, prompt/tokenizer counts, answers, verifier results, runtime
versions, and source hashes. The external watchdog logs independently record
their resource samples and successful process exits.

## Admission and next experiment

The snapshot download used a 10,000,000,000-byte reservation and the 0.8B
repeat used a separate 100,000,000-byte reservation. Both included the Docker
WSL model volume and hourly automation directory. C: retained more than 134 GB
free; aggregate Wrench storage remained below the 50 GB limit. The downloaded
2B snapshot remains under `C:/wrench-slm-data/weights`.

The next token-savings task is a typed compact source-label serialization.
Iteration 141 measured a tokenizer-only 94.190807% reduction for a compact
label/text-block variant, 156 tokens above 95%, but it was not implemented or
checked for collisions, prompt injection, or model answers. Implement it from
the selected-source records while keeping exact path/span provenance in the
external receipt, then measure it on the same task set and expand the
answer-blind battery beyond three lookups. Next, prepare a separate 2B LoRA
package and fit estimate; train only after its exact package review and the
25% RAM training-start gate. The held-out split stays sealed.

## Failed attempt

An initial local-inventory pass invoked `git hash-object` on the 4.55 GB shard
before checking its upstream LFS SHA-256, reading the shard in tiny blocks and
making no output. I stopped only that verification process and switched to
the existing verifier's 8 MiB buffered hash path. The verified inventory
above is the accepted result; the interrupted pass is not a pass.

## Sources

- [Prior model-size evidence and external LoRA/compression research](../../reports/wrench-gateway-model-research/model-size-decision-refresh-iter143-20260928.md)
- [Iteration 140: exact symbol-span paired result](iteration-140-exact-symbol-span-paired-20260928.md)
- [Iteration 141: prompt-envelope ablation](iteration-141-prompt-envelope-ablation-20260928.md)
