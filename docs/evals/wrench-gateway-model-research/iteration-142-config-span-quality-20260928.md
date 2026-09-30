# Iteration 142: configuration-span quality and token tradeoff

Date: 2026-09-28 (America/Edmonton)  
Assignment: WRENCH-CONFIG-SPANS-PAIR-ITER142  
Status: **table spans preserved 3/3 tiny synthetic checks at lower savings than Iteration 140; assignment-key spans reduced savings and verified only 1/3; neither is frontier-token or product evidence**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Updated gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question and change

Could required configuration files be narrowed to a relevant TOML table or
individual assignments while retaining the exact evidence needed by a small
local model? The E0 pipeline received an opt-in required-path TOML key-span
mode, source references identify parser-reported TOML assignment lines, and
the demo runner enabled the key-span mode alongside exact symbol spans. The
work was limited to TOML-shaped synthetic fixture cases.

The focused tests had already passed before the paired runs:
`tests/test_toml_context_spans.py`, `tests/test_e0_context_pipeline.py`, and
`tests/test_selected_segment_sources.py`: **35 passed**. The report does not
claim broader integration or task utility from those unit checks.

## Paired results

Both paired runs used the same three authored lookup tasks and fixture
(`92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`), the
same Qwen/Qwen3.5-0.8B BF16 snapshot at revision
`2fc06364715b967f1860aea9cf38778875588b17`, and no adapter. The full-context
arm verified 2/3 cases in each receipt.

| Context strategy | Wrench verified | Local input reduction | Local input + output reduction | Target-tokenizer input reduction |
|---|---:|---:|---:|---:|
| Exact symbol spans, Iteration 140 | 3/3 | 95.232% | 95.138% | 92.123% |
| Relevant TOML table spans, Iteration 142 R2 | 3/3 | 94.591% | 94.498% | 91.515% pooled from 1,637 / 19,297 tokens |
| Individual TOML assignment lines, Iteration 142 | 1/3 | 92.434% | 92.343% | 89.403% pooled from 2,045 / 19,297 tokens |

The table-span receipt records all three Wrench answers verified, compared
with two of three in its full-context arm. This is a three-case observation,
not a reliable quality estimate. It used more input than the Iteration 140
symbol-span result, and it did not reach 95% target-tokenizer reduction.
The individual-line receipt preserved all required quote checks (7/7), yet
the model reversed or misassociated configuration values in two answers. Its
strict verifier accepted only one of three. This is direct evidence that quote
visibility alone does not establish answer quality and that assignment-level
compression can remove helpful relationships or ordering cues.

The exact assignment-line strategy should not be enabled in the demo's default
path based on this evidence. Keep the existing opt-in implementation as a
diagnostic until a larger, independently frozen config workload and recovery
checks establish a benefit. The table-span arm is the better config result in
this tiny comparison, but it does not replace exact symbol spans as the best
measured variant. Do not combine component percentages or treat local-tokenizer
reductions as provider savings.

After comparing the paired receipts, the demo runner's TOML key-span opt-in was
removed. The default now preserves the full required configuration file while
continuing to use parser-verified symbol spans for code. The TOML parser and
explicit E0 opt-in remain available for separately admitted experiments. The
final runner SHA-256 after this change is
`F7F588053E48E34C356D4D35102C0D8E526043A5A5EABA0511EA934CC22420D4`.
The focused 35-test command passed again after the change; `git diff --check`
also passed.

## Receipts and identities

| Item | Bytes | SHA-256 |
|---|---:|---|
| Key-line paired receipt `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter142-config-keys.json` | 6,100 | `AE3EFE186B5EE85E84497532B19091A14E1D339212A2D7011224603FD42608E2` |
| Table-span paired receipt `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter142-config-tables.json` | 6,103 | `F906633EEAA6A8BA3EDBF9BD9E88C012EEF574E57B650D99037AACF99D0EA9E8` |
| `src/wrench_harness/e0_context_pipeline.py` | — | `C7064CE54EA8FB3218515454DE7E33E8012E7B1352D00F5E9AE7266D39266190` |
| `src/wrench_harness/toml_context_spans.py` | — | `4F42B564D9A0D54F1F6717142807AC430969BB5A82C69F560F49E35A9705ACF5` |
| `src/wrench_harness/selected_segment_sources.py` | — | `DDA74BFAD5E9E86EEB440AF0C21614A1A2375E03278FE24443DA84A66D2265DD` |
| `examples/gateway_context_mvp/run_local_model_mvp.py` (final after default-off repair) | — | `F7F588053E48E34C356D4D35102C0D8E526043A5A5EABA0511EA934CC22420D4` |
| Updated gateway goal | — | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |

The key-line receipt reports 55 resource samples, minimum free RAM 13.379%,
minimum free VRAM 75.471%, no monitor errors, no frontier calls, and $0
provider spend. The table-span receipt reports minimum free RAM 13.618%,
minimum free VRAM 75.250%, no monitor errors, no frontier calls, and $0
provider spend. Each is a local 43-second synthetic run. The key-line paired
receipt's exact Wrench arm score is 1/3; its paired baseline is 2/3.

## Limits and next action

The workload has three synthetic lookup cases over repetitive configuration
and log material. It does not measure trained-LoRA behavior, real repository
engineering, frontier calls avoided, full-lifecycle frontier tokens, all-in
cost, confidence bounds, or an all-day session. The file contains no real or
consented workflow data. The current SubRoute provider route was not called.

The owner-directed goal was updated in this iteration to require a 0.5B-12B
evidence-based model-size recommendation first, then the highest verifiable
full-lifecycle savings consistent with every existing acceptance gate, then
resumption of mechanical/context engineering. The 10B-12B range remains
research-only without separate execution authority. This edit changed the
gateway goal hash; Fit-03's prior exact-package static review is historical
only and must receive a fresh review before any fit. No fit, download,
provider request, held-out read, activation, or route change occurred.
