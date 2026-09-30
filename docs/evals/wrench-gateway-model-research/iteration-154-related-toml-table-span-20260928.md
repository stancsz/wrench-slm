# Iteration 154: related TOML table spans on Qwen3.5-2B

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-RELATED-TOML-TABLE-SPAN-ITER154-20260928`  
Status: **TOML table preservation is implemented and tested, but the aggressive table arm is rejected for a repeatable retry-count error and still misses 95% target-tokenizer input reduction.**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question and method

The prior 2B related-path arm retained the complete `config/service.toml` and
selected Python symbols. It verified all three known development cases, but
used 1,096 of 19,297 target-tokenizer input tokens (94.320361% reduction).
This iteration added an opt-in TOML table-span arm that retains a selected
table's exact header and complete assignments, binds the span to the same
snapshot/source hash, and falls back to whole-file evidence when the TOML
contains unsupported syntax. The comparison reused the Iteration 153 frozen
synthetic fixture, requests, answer-blind path manifest, Qwen3.5-2B revision,
decoding, verifier, and compact prompt format. No held-out data was opened.

An independent design review found that the previous key-span mode exposed
the assignment but not its table header. The new mode makes table identity
visible. Its query matcher counts distinct query terms per table, not repeated
matches of a table name on each assignment; a table must match at least two
distinct terms. Unsupported tables fail closed to the caller's full-file path.

## Paired local results

| Arm | Target tokenizer input | Local model input + output | Verified |
|---|---:|---:|---:|
| Full fixture | 19,297 | 26,221 | 3/3 |
| E0, all fixture paths | 1,162 (93.978339% reduction) | 766 (97.078677% reduction) | 3/3 |
| E0, answer-blind related paths | 1,096 (94.320361% reduction) | 694 (97.353266% reduction) | 3/3 |
| Related tables, initial matcher | 1,023 (94.698658% reduction) | 607 (97.685062% reduction) | 2/3 |
| Related tables, distinct-term matcher | 977 (94.937037% reduction) | 561 (97.860493% reduction) | 2/3 |

Both table runs failed `retry-policy`: the model returned `2,250`; the frozen
oracle is `3,250`. The other cases returned `1800,300` and
`calculate_retry_delay`. R2 removed the unrelated `[http]` timeout table and
reduced target-tokenizer input by another 46 tokens, but the retry answer did
not recover. This error also occurred in Iteration 152's config-only path arm.
It is therefore a repeatable failure of this narrowed context on the known
case, not an accepted tradeoff. Keep the table arm disabled for this workload
until context or routing restores verified quality.

The R2 target-tokenizer count is 977/19,297, still 12 tokens above the <=964
needed to reach 95% on this three-case input proxy. The 97.860493% local-model
token reduction includes local prompt and output counts; it is **not** a
Frontier-token reduction. No provider request was made, so Frontier savings,
route rate, paid cost, and all-in cost remain unmeasured. There was no trained
LoRA in any arm.

## Exact run identity and resources

R2 used `Qwen/Qwen3.5-2B`, revision
`15852e8c16360a2fea060d615a32b45270f8a8fc`, BF16, Python 3.13.15, PyTorch
2.14.0+cu132, Transformers 5.17.0, CUDA 13.2, and an NVIDIA RTX 5060 Ti with
16,311 MiB VRAM. The model inventory SHA-256 is
`23e0d5f79e57d41ab9f007b697d8f75f56f5f528519bfdf15f406e1f28df3dd5`; the
snapshot verification receipt SHA-256 is
`59d1d57dfd5a4ca4c525c926bd507b11634969ec7e473d4378649203c2120014`. Adapter:
none. The pinned offline add-on directory supplied `accelerate`.

The R2 run loaded in 11.7158 s and took 63.5549 s overall. Across 80 resource
samples, minimum free RAM was 11.7538% and minimum free VRAM was 61.4187%; the
10% runtime floors were maintained. This confirms this exact 2B BF16 inference
path completed on this host with narrow RAM margin; it does not establish
LoRA-training fit or smooth all-day coding work. Fallback attention kernels
were used because optional optimized kernels were absent.

The first launch attempt exited before model loading because its invocation
omitted the already-approved `WRENCH_LORA_ADDONS` path and could not import
`accelerate`. It produced no receipt or model output. The failed reservation
was released after confirming termination and no output. The successful run
used a new job ID and reservation.

## Tests and artifacts

The focused tests passed after the final matcher change: **40 passed** across
`test_toml_context_spans.py`, `test_e0_context_pipeline.py`, and
`test_selected_segment_sources.py`. They cover table headers, exact source
lineage, repeated keys, unsupported TOML fallback, and distinct-term scoring.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-related-table-span-iter154-rerun01-qwen35-2b.json` | 31,630 | `A872CCA379086CEB3E3E546010751DC3C199FF49627A583E26419574972E0547` |
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\paired-related-table-span-iter154-rerun02-qwen35-2b.json` | 30,135 | `E23071D74AFA658DF4287E9CF544EBA61D07350AD051626443522AA957A97450` |

Storage included `C:\\wrench-slm-data`, both Wrench worktrees, the hourly
automation directory, and the Docker WSL model volume; admission remained
below 50,000,000,000 bytes. Both run reservations were released after process
termination and output hashes/bytes were recorded. No credentials, SubRoute
configuration, spending, or external provider were accessed.

## Decision

Keep the header-preserving table extractor as an opt-in experiment mechanic,
but reject the current aggressive table arm for the retry task. The safe
answer-blind related-path arm remains the best verified arm on these three
cases at 94.320361% target-tokenizer input reduction, not 95%. Model-size
selection remains provisional: Qwen3.5-2B has completed this battery but
failed the narrowed retry case; there is still no same-runner 0.8B/2B
comparison with an evaluated Wrench LoRA, no Frontier usage pair, and no
all-day engineering evidence.

The next useful comparison is the same frozen battery on the 0.8B control,
then a context/routing arm that restores the retry-policy verifier without
giving up the required token margin. Keep every failed result and do not
open the sealed held-out split.
