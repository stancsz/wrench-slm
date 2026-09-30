# Iteration 204: Qwen3.5-2B LoRA paired synthetic dev score

Date: 2026-09-29  
Job: `WRENCH-QWEN35-2B-DEV-SCORE-20260929-01`  
Review: `WRENCH-GATEWAY-ITER204-2B-SCORE-PACKAGE-REVIEW-20260929-02`, nonce `9c720884-a19a-4de6-8419-d99f83e06154`  
HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Disposition: **score completed; the LoRA candidate fails this development diagnostic and remains inactive.**

## Paired result

The exact pinned Qwen3.5-2B base and its rank-8 Wrench LoRA received the same 64 prompt-only synthetic development rows. Predictions were persisted and hashed before the dev-only oracle was read. An independent reviewer checked the receipt, predictions, and identities and reconstructed the preflight answer. The held-out split was not accessed.

| Measure | Base | Wrench LoRA |
|---|---:|---:|
| Exact five-field decisions | 16/64 (25.0%; Wilson 95% CI 16.0%-36.8%) | 8/64 (12.5%; Wilson 95% CI 6.5%-22.8%) |
| Compaction policy | 0/16 | 0/16 |
| Evidence selection | 16/16 | 0/16 |
| Retrieve/stop | 0/16 | 8/16 |
| Route family exact | 0/16 | 0/16 |
| Valid schemas | 64/64 | 49/64 (76.6%) |
| Route field correct | 36/64 (56.3%) | 30/64 (46.9%) |
| Authority violations / invalid evidence IDs | 0 / 0 | 0 / 0 |
| Frontier route proposals | 0/64 | 4/64 (6.25%) |
| Invalid / abstain route outputs | 0 / 0 | 2 / 2 |
| Exact-decision latency mean / p95 | 22.71 s / 27.01 s | 19.77 s / 24.78 s |

On paired exact decisions, the LoRA won 8 rows, lost 16, and tied 40, for a -12.5 percentage-point change (8/64 versus 16/64). Its eight retrieve/stop wins did not offset losing all 16 evidence-selection cases, all 16 compaction cases, and all 16 route-family cases. This adapter is not a viable Wrench controller on this screen. The synthetic results do not rule out all 2B adapters or other training data, but they contradict promoting this fitted candidate.

The scorer defines an exact decision as full parsed-object equality, including the order of selected_evidence_ids. The family rows above are exact five-field decisions; this report does not add a post-hoc set-based evidence-selection score. If selected-ID order is not semantically binding in the product contract, evaluate that metric in a predeclared follow-up without replacing these recorded exact results.

The base predicted `LOCAL_MECHANICAL` for every row despite getting only 25% of complete decisions correct. This shows why a low apparent route rate alone is not evidence of useful local task completion. The LoRA proposed Frontier for four rows, above the 5% screen target, but no actual Frontier call was made. This is a prediction count on a small synthetic dev set, not a measured episode escalation rate.

## Size decision update

The same frozen dev prompts support a provisional shift in experiment priority from 2B to 4B, while leaving the overall size winner undecided:

| Model and arm | Exact decisions | Schemas valid | Route field correct |
|---|---:|---:|---:|
| Qwen3.5-2B base | 16/64 | 64/64 | 36/64 |
| Qwen3.5-2B LoRA | 8/64 | 49/64 | 30/64 |
| Qwen3.5-4B base | 18/64 | 64/64 | 55/64 |
| Qwen3.5-4B LoRA | 26/64 | 59/64 | 48/64 |

The 4B LoRA is the stronger current candidate on this particular synthetic decision screen: it reached 40.6% exact decisions and improved over its base, while the 2B LoRA regressed. But the 4B result still has zero exact route-family and retrieve/stop decisions, five invalid schemas, and only 40.6% exact accuracy. It does not establish a model for the full product, real repositories, or all-day engineering. See [Iteration 197](iteration-197-qwen35-4b-dev-score-results-20260929.md). Keep both adapters inactive pending a new reviewed candidate and a broader, representative evaluation.

On the RTX 5060 Ti, this exact 2B score completed in 2,819.44 seconds (46 min 59 s) with no timeout. Across 2,219 samples, minimum free RAM was 22.46%, minimum free VRAM was 10,643/16,311 MiB (65.25%), scratch peak was zero, and no resource-floor breach was recorded. This establishes that this bounded fit and score ran safely on this host; it is a slow diagnostic and does not prove smooth interactive service or sustained all-day engineering. Mean scorer latency was about 20-23 seconds per generated decision, with p95 about 25-27 seconds.

## Token and product claims

Both arms counted local tokenizer input as 22,921 tokens. Local completion counts were 4,894 base and 3,892 LoRA. Those are local diagnostic counts, not Frontier usage. The run made zero Frontier calls; provider input/output usage, billed tokens, token savings, all-in cost, task completion rate, and success retention remain **unmeasured**. No 95% claim passes. The separate Iteration 197 context-pruning figures of 94.32% and 94.94% are three-task local target-tokenizer proxies, not this LoRA score and not provider evidence.

## Exact identities

- Base: `Qwen/Qwen3.5-2B`, revision `15852e8c16360a2fea060d615a32b45270f8a8fc`.
- Model inventory SHA-256: `23E0D5F79E57D41AB9F007B697D8F75F56F5F528519BFDF15F406E1F28DF3DD5`.
- Fit job: `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-FIT-20260929-03`; 96 optimizer steps, 256 synthetic train rows, 64 dev diagnostic rows.
- Adapter SHA-256: `1B679FEE96C31B066C9AD5D8912FD4A2BC024FF8665BE20B957D878CED8EBD41`.
- Evaluator SHA-256: `8981E12EA53C2F3991027B519F68803492E5EF67A25AAAEDF0D823505B0E24D1`.
- Evaluation protocol SHA-256: `AF5E9325D077B619F632270B2A37237AE28623965D216F7892AAA856F84BB35C`.
- Preflight receipt SHA-256: `0F1D21439A623798628BCB6F898B0EAE1A085BC600A7FC20582ABD516513BF28`.
- Result receipt SHA-256: `13BBFC1EF706F8D1B43910E7253FEC6955B3E76C0FD50B983D4A55DBAB630785`.
- Base predictions SHA-256: `9A8FE95B6B07D75F947F4D711475B5A29BDCA0C28EB32BD63CE380C230CE8873` (64 rows).
- LoRA predictions SHA-256: `C042C2EF7A8F3E76845AA6766EA6DA36A0470A64671EC0E63D509CE617C9CAC5` (64 rows).
- Resource log SHA-256: `4799DAB2BE66A0A477EBCCC9BCC689B18C55906A6DCBF499321FE560DC1DCD9A`.
- Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, PEFT 0.21.0, Accelerate 1.15.0.
- Device: NVIDIA RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`, 16,311 MiB VRAM.
- Storage reservation: 1,000,000,000 bytes; released after the process stopped and all outputs were counted.

This is a synthetic development diagnostic with a broad 64-row uncertainty interval, not a holdout or representative coding evaluation. The next size decision should focus on whether a revised 4B controller can correct its route and retrieve/stop failures without schema regressions, and whether context reduction preserves verified coding-task outcomes. Use actual provider usage receipts only after a separately authorized spend cap exists.

