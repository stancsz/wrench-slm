# Iteration 151: compact prompt provenance binding

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-COMPACT-PROVENANCE-2B-RERUN-ITER151`  
Status: **Three-case 2B compact-context rerun passed; all three durable case receipts now bind the exact rendered prompt, ordered E-label mapping, and selected-source receipt. This is provenance evidence only.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Change

The compact E0 runner now checks that generated labels `E1..En` map to the
selected segment IDs in order, that the content-free source-reference receipt
contains those same IDs in the same order, and that its canonical digest is
valid. For each compact case it writes the exact chat-template prompt SHA-256,
the label-to-segment map, the full content-free source-reference receipt, and
a binding digest over those identities. The source references contain paths,
hashes, parser spans, and artifact handles, not source text.

The checks fail closed on missing sidecars, a reordered label map, reordered or
swapped references, and modified source data without an updated receipt hash.
Four focused standard-library unit tests passed. `pytest` is not installed in
the available Python environments, so the test ran with `unittest` using the
local synthetic environment. `git diff --check` passed; Git reported only the
repository's existing mixed-line-ending warnings.

## Paired rerun

The exact Qwen/Qwen3.5-2B snapshot from Iteration 149 was run with compact E0
on the same three authored synthetic lookup cases. Identity was revision
`15852e8c16360a2fea060d615a32b45270f8a8fc`, inventory SHA-256
`23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5`, and
snapshot-receipt SHA-256
`59d1d57dfd5a4ca4c525c926bd507b11634969ec7e473d4378649203c2120014`.
Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2,
RTX 5060 Ti, BF16. No adapter was loaded and no provider was called.

| Measure | Result |
|---|---:|
| Full-context answers verified | 3/3 |
| Wrench compact-context answers verified | 3/3 |
| Target tokenizer input | 26,196 → 741, 97.171324% lower |
| Local model input plus output | 26,221 → 766, 97.078677% lower |
| Runtime including model load | 51.0779 s |
| Minimum sampled free RAM / VRAM | 13.9769% / 61.3145% |
| Compact cases with validated provenance bindings | 3/3 |
| Frontier calls / spend | 0 / $0 |

The input totals reproduce Iteration 149. This rerun validates the receipt
schema and 2B path but does not raise the measured compression result. The
three-case sample is not coding success, LoRA quality, all-day reliability,
frontier-token savings, 95/5 routing, success retention, or all-in cost proof.

## Artifacts

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-compact-iter151-qwen35-2b.json` | 13,492 | `CB53DA82ADCFF271CEE037CD1E40420100F30D58C38A9FE203C8CBBF16DC52C9` |
| `examples/gateway_context_mvp/run_paired_local_context_baseline.py` | — | `5FAFCC5F52B490BFA78F1E289C8B40EEFC851155E72A0E0081881D9D2EA1956C` |
| `tests/test_gateway_compact_provenance_receipt.py` | — | `127C446514FC95BC071A1A3D54893A477352A0C393185631D203E38AFC261059` |

The independent review for assignment
`WRENCH-COMPACT-PRUNING-INDEPENDENT-REVIEW-ITER151` (nonce
`707d3aa1-5f5a-42ec-8290-10cb07153c81`) agrees that compact source lineage is
credible when the sidecar stays joined to the rendered prompt, and cautions
that hashes establish integrity rather than authenticity. It also confirms the
Iteration 148 quote-selected 95.185780% input result is diagnostic because it
uses expected-quote annotations. Next pruning evidence must select required
spans before model answers exist, fail closed on stale hashes, and retain exact
hot evidence plus audited recovery. No source text, sealed data, credentials,
or SubRoute were accessed in this iteration.
