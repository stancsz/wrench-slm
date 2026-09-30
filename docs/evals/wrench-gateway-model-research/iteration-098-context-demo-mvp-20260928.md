# Iteration 098: deterministic gateway context demo MVP

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-DEMO-MVP-001-20260928`  
Status: **three-case synthetic E0 context-preparation demo passed; product utility remains unproven**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway goal SHA-256: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Result

The reproducible entry point is [the demo README](../../../examples/gateway_context_mvp/README.md)
and [`run_demo.py`](../../../examples/gateway_context_mvp/run_demo.py). It
creates a temporary synthetic service repository, executes the current Wrench
E0 snapshot, structural selection, artifact store, bounded context assembly,
and prompt serialization path, then counts the resulting messages with the
pinned MiniMax M3 chat template.

| Case | Baseline input tokens | E0 prepared input tokens | Input reduction | Required quotes visible |
|---|---:|---:|---:|---:|
| Retry policy | 6,433 | 1,107 | 82.7919% | 3/3 |
| Session lifetime | 6,428 | 924 | 85.6254% | 2/2 |
| Retry function | 6,428 | 586 | 90.8836% | 2/2 |
| **Pooled, ratio of sums** | **19,289** | **2,617** | **86.4327%** | **7/7** |

This is exact input-token reduction for three synthetic E0 preparation cases,
not observed frontier usage. The fixtures include 240 repetitive synthetic
health-log lines, so the result specifically measures a context workload with
substantial irrelevant log volume. There are no real coding tasks, generated
answers, verifier outcomes, local-model calls, provider calls, billed dollars,
or LoRA contributions. `frontier_token_savings_percent`, `task_completion`,
and `billed_cost` are explicitly null. The result does not establish the
95/5/95 targets, 95% cost reduction, or all-day engineering reliability.

The latest measured receipt is
`C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\demo-receipt.json`,
3,818 bytes, SHA-256
`E00A11E197DD18C7756F80AD1B1F4C472B41B7B069FA69DE144C2D0CF2316AF5`.
It binds the authored-fixture hash
`92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`, pinned
`MiniMaxAI/MiniMax-M3` revision
`f0e1c1e04d40177e4673a22097036854f536e9c0`, tokenizer inventory hash
`86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`, chat
template hash `11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64`,
and tokenizer runtime versions (`transformers 5.17.0`, `tokenizers 0.23.2`,
`huggingface-hub 1.33.0`). The context token budget was 1,024. Per-case
baseline/prepared prompt hashes and exact source/snapshot identities are in
the receipt.

## Engineering finding and repair

The symbol-targeted path had not been exercised by this MVP. It failed closed
because `ContextLedger` requires string-valued metadata while E0 supplied
integer `start_line` and `end_line` values for an exact symbol segment. E0 now
serializes those line numbers as strings. The same path also places its
required full-file evidence after the bounded structural-candidate source
order range so each ledger segment receives a unique order. The three-case
demo then completed, retained all seven required quotes, and measured exact
input counts.

Early demo attempts exposed the bytes/string boundary in the sample's quote
check and the symbol-metadata failure; failed attempts generated no usable
receipt and their temporary repositories were removed. The successful receipt
is from the current E0 source hash below. A focused regression test was added
to [`test_e0_context_pipeline.py`](../../../tests/test_e0_context_pipeline.py)
but could not be run: both the demo environment and PATH Python return `No
module named pytest`, and the supplemental add-ons directory has no
`Scripts/python.exe`. The full end-to-end demo is the runtime verification for
this path; `git diff --check` returned exit 0 with existing line-ending
warnings only.

## Exact measured source identities

| Source | SHA-256 |
|---|---|
| `src/wrench_harness/e0_context_pipeline.py` | `f28378dd6712738506918d23fd34e121e4efe9c05a0f5020267eb3a38fe74251` |
| [`examples/gateway_context_mvp/run_demo.py`](../../../examples/gateway_context_mvp/run_demo.py) | `9e05a8822919cb1825e48fb4895db5c1d84f649ee6e2573252bf8f708c69ddf3` |
| [`tests/test_e0_context_pipeline.py`](../../../tests/test_e0_context_pipeline.py) | `2902c40da9a712705811db34638cc8f9aa67ba13b2aea03dccbff58ef9e8939e` |

The receipt lists hashes for the rest of the E0 pipeline files. Base revision
is `af01304824f079a64b6c3902397a2034b843511a`;
`working_tree_dirty=true`, so neither the base commit nor a passing synthetic
demo alone certifies the entire dirty tree.

## Resource and spend accounting

No model weights were loaded and no model/provider request was sent. Peak
observed system RAM stayed above 26% free; peak GPU report was above 15,200 of
16,311 MiB free. Storage admission included the repository, `C:\wrench-slm-data`,
Docker's WSL model volume, the active Codex automation directory, all known
Wrench siblings and the legacy external source snapshot. The checker remained
`WITHIN_LIMIT` below the strict 50 GB aggregate ceiling. The demo had a unique
10,000,000-byte reservation; C: had over 144 GB free. Temporary fixtures were
removed at exit; the 3,818-byte receipt and source additions are counted in
the final storage status before releasing the reservation.

SubRoute read-only health was HTTP 200 and its active route remained forced
OpenRouter (policy 4). No completion was sent and no route was changed. The
campaign-wide numeric spend cap is still absent.

## Next step

The 86.43% component result is below neither a frontier-token measurement nor
the full product target; it is not a 95% result. Continue with the exact
lowered-request/tool-schema path and paired coding episodes, keeping all
verification/retries/recovery fetches in the account. Before measuring LoRA
utility, rerun the added focused regression test in an approved environment
with `pytest`, review the changed E0 source against the current goal hash, and
keep the Qwen3.5-2B LoRA as a research lead only. Training, spend, held-out
access, and activation were not authorized by this iteration.
