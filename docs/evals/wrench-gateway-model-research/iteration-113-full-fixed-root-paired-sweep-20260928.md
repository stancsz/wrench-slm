# Iteration 113: full paired sweep on the original stable source root

Date: 2026-09-28 (America/Edmonton)  
Assignments: `WRENCH-E0-REQUIRED-SOURCE-PRIORITY-PAIRED-ITER113-20260928`, `WRENCH-E0-CONTEXT-REPRO-ITER113-FULLRANGE-20260928`  
Status: **paired selection fix passed all 897 settings on the exact Iteration 111 source identity; highest verified synthetic prompt-input reduction is 90.694178%**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Paired result

This follow-up reused Iteration 111's exact stable source directory, artifact
stores, fixture bytes, and snapshot identity, then ran the updated E0 source
selection code at every budget from 128 through 1024. This isolates the code
change from the source-root identity change in Iteration 112.

| Paired measure | Before, Iteration 111 | After, Iteration 113 |
|---|---:|---:|
| Same-source settings tested | 897 | 897 |
| Context preparations ready with all required quotes | 824 | 897 |
| Fail-closed required-evidence omissions | 73 | 0 |
| Prior failures recovered | -- | 73/73 |
| Prior successes lost | -- | 0/824 |
| Snapshot identity | `2f7dd68f4b336e1b30769685d26c857634fed353edd57ce3c292d7c67e8e9256` | same |

The fix makes required evidence IDs mandatory before optional retrieval
candidates consume the context budget. The prompt compiler's final required
evidence gate remains in place. The pass/fail improvement is paired on the
same snapshot identity; it is not a comparison between different model or
tokenizer runs.

## Highest measured setting

The highest ratio-of-sums final prompt-input reduction across the full sweep
was **90.694178%**, tied at context budgets 134 and 135. At budget 134, the
three synthetic cases went from 19,289 to 1,795 input tokens. All seven
required quotations remained visible. Three repeat runs returned exactly the
same baseline/prepared counts, three snapshot hashes, and three prompt hashes.

| Case | Baseline tokens | Prepared tokens | Required evidence |
|---|---:|---:|---:|
| Retry policy | 6,433 | 613 | 3/3 quotes |
| Session lifetime | 6,428 | 608 | 2/2 quotes |
| Retry function | 6,428 | 574 | 2/2 quotes |
| **Pooled** | **19,289** | **1,795** | **7/7 quotes** |

These use the pinned MiniMax M3 chat template to count complete serialized
prompts. The selector's active context budget still uses `word_estimate_v1`,
not the target tokenizer. This is deterministic prompt-input reduction on
three synthetic tasks with 240 repetitive authored log lines. It is not a
frontier request measurement, local-model outcome, generated-code success,
LoRA gain, or a measure of all-day work.

## Exact identities and receipts

Source snapshot SHA-256:
`2f7dd68f4b336e1b30769685d26c857634fed353edd57ce3c292d7c67e8e9256`.
Fixture SHA-256:
`92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
Tokenizer: `MiniMaxAI/MiniMax-M3@f0e1c1e04d40177e4673a22097036854f536e9c0`.
Tokenizer inventory SHA-256:
`86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`.
Chat-template SHA-256:
`11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64`.
Updated E0 pipeline source SHA-256:
`4ea3e320eaba9dfa0fcbc3686e4ededc432ac7b06631a9132a06219f9c463c04`.

The full machine receipt is
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\iter113-full-fixed-root.json`,
896,411 bytes, SHA-256
`d74ede9097f854ab8b023d49c98082eff07232f7dca74e0aee6c271d8cf459ef`.
It binds all 897 current rows, each prior status, the prior receipt hash,
source-code hashes, and three winning-setting confirmations. Its final
progress checkpoint is
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\iter113-full-fixed-root.progress.json`,
891,777 bytes, SHA-256
`028d54624641879d9e18251dda86c937b1872e7eb808160526c07b9c0c908196`.

The initial direct paired slice over budgets 128-224 is separately retained at
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\iter113-paired-root-priority.json`,
96,243 bytes, SHA-256
`43daac813e81898d209cb9a61dee7604087ca688cecc1840c7ce4002c190fcba`. The
prior Iteration 111 receipt is 834,362 bytes, SHA-256
`09bc1254cbc8dbb244eaee87c79849fe66fcd7bbfff5272734613811dac3de61`.

An identity supplement joins the full result receipt to the exact synthetic
tasks, system messages, demo harness, and tokenizer-measurement source:
`C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\iter113-full-fixed-root-identity.json`,
3,635 bytes, SHA-256
`79ba08102aa8ae660742e4d30d31a8ccf1d987faaa6c783239cfe1f945e6e46c`.
Task-definition canonical SHA-256:
`aab5e1a90b9f55f0a1c16e34fe93092e1d6c81428954c3184ada0bad7ab6cc77`.
Base-message canonical SHA-256:
`f7c792e3affb13d589d61962603ae6ae99e18897b195988748558c3344e08be3`.
The inline sweep-driver code was not captured as a standalone file or hash;
the identity supplement records that limitation. The receipt and its
supplement preserve the evaluated outcomes and inputs, but a future repeat
should use a committed, hash-bound driver.

## Interpretation and next gate

This raises the best verified Wrench synthetic prompt-input reduction from
89.227021% to 90.694178%, a 1.467157 percentage-point gain against the same
frozen source identity. It does **not** establish the product's 95% frontier
token target: no model or provider ran, and there are no matched coding-task
outcomes, frontier usage receipts, retries, or billed-cost rows. It does not
prove the 95/5 completion and routing targets, success retention, all-in cost,
or reliable all-day engineering.

The focused regression is in `tests/test_e0_context_pipeline.py`. The approved
runtime environments do not contain pytest, so the regression was executed
directly through `prepare_e0_context`; the committed test remains for CI. The
scan used no model inference and no GPU compute. Lowest sampled free RAM was
16.16%; GPU free memory remained above 15,200 MiB of 16,311 MiB. Storage checks
included the Wrench repository, approved data root, Docker WSL model volume,
and hourly automation directory and remained within the 50 GB ceiling.

Next, run the focused pytest in the normal CI environment and measure
task-level correctness on a rights-cleared, frozen coding workload. Keep the
small-controller/model-size choice provisional until its Wrench LoRA beats the
deterministic baseline after overhead. Fit-03 still requires at least 25% free
RAM at start; provider calls through SubRoute `:4000` remain closed pending an
enforced numeric campaign cap.
