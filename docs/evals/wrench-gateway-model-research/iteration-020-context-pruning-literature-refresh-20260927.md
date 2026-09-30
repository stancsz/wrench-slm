# Iteration 020: coding-agent context compression literature refresh

Date: 2026-09-27

Status: primary-source literature review complete; no Wrench model-effectiveness measurement

## Question

Which realistic small-model and deterministic context-management approach is
most likely to reduce gateway work while preserving engineering quality, and
does current evidence support the joint Wrench targets of at least 95% task
retention and at least 95% frontier-token savings?

## Findings

| Source | Published result | Relevance and transfer limit |
| --- | --- | --- |
| [SWE-Pruner](https://arxiv.org/abs/2601.16746) | A 0.6B Qwen3-Reranker-based skimmer uses CRF pruning and reranking heads trained on 61K synthetic examples. It reports 23%-54% token reduction on multi-turn SWE-Bench Verified/SWE-QA tasks and up to 14.84x on single-turn LongCodeQA. | Closest size reference for task-conditioned line selection. Its custom CRF/reranking architecture is not a Wrench LoRA. The multi-turn results are well below 95% reduction; the single-turn maximum does not establish agent-loop savings. |
| [Paritok-4B](https://arxiv.org/abs/2608.24188) | A Qwen3-4B LoRA compressor uses typed segments and current intent. On 300 SWE-Bench Lite examples, it retained 25.7% of context (74.3% reduction) with 86.5% of uncompressed single-shot solve quality. Line-numbered inputs retained 27.8% of context with 89.3% quality. | Strongest direct LoRA compression analogue found. It is a single-shot comprehension harness, not end-to-end multi-turn economics. Its 24 GB deployment target exceeds this host's 16 GB VRAM. The reported McNemar result does not prove parity or noninferiority. |
| [SWE-Pruner Pro](https://arxiv.org/abs/2607.18213) | An 18M auxiliary head reads large coding backbones' last-layer states. On Qwen3-Coder-Next, input tokens fell 13.5% with six fewer solves out of 500 (-1.2 percentage points), while API calls rose from 131.9 to 139.8. On MiMo-V2-Flash, solves rose 3.8 points but input tokens rose 7.4% and calls rose. | Shows backbone-specific relevance signals may support a small pruning head, but serving requires exposed hidden states and patched SGLang. Quality and cost effects vary by backbone; token-only deltas are insufficient. |
| [ACON](https://arxiv.org/abs/2510.00615) | Reports 26%-54% lower peak-token use on long-horizon AppWorld, OfficeBench, and multi-objective QA tasks, and distills compression guidelines into smaller models. | Supports teacher-guided compression-policy distillation. The abstract does not establish >95% teacher-performance retention; benchmarks are not repository coding. |

## Decision

The practical Wrench design to test is deterministic retrieval and accounting
plus a small, Wrench-specific LoRA that proposes bounded, task-intent-conditioned
selection of source-backed lines or typed segments. Preserve originals and
exact source identity; allow deterministic recovery; protect hot spans; count
tokens, retries, verification, latency, local compute, and human rescue. Keep
the model away from arbitrary shell, code mutation, credential, and permission
authority.

Use the already staged Qwen3.5-0.8B as the first controller candidate because
it is the smallest compatible experiment already prepared. Compare Qwen3.5-2B
only if a frozen held-out result demonstrates a capacity failure. SWE-Pruner's
0.6B method is an architectural reference, not a Wrench LoRA result.
Paritok-4B is a useful compression-quality reference, but it exceeds the
currently observed GPU envelope. Do not infer repository coding ability from a
context-selector score. Evaluate any coding worker separately on paired real
engineering episodes with tests and verified outcomes.

The literature found here does **not** support a claim that a small model can
do at least 95% of frontier work while using 95% fewer frontier tokens and
costing 95% less all-in. The best directly relevant reported operating points
are roughly 23%-54% multi-turn token reduction, or 74% context reduction with
86%-89% single-shot solve-quality retention. These are independent papers and
benchmarks, not Wrench measurements. The original joint claim remains an
empirical hypothesis.

## Run boundary and resources

- No model download, load, inference, LoRA fit, or packaging ran.
- SubRoute `http://127.0.0.1:4000` stayed read-only and force-routed to
  `openrouter`; no generation POST was sent. A numeric aggregate spend cap is
  still not recorded.
- Latest host sample: 3,843 MiB free of 32,702 MiB RAM (11.75%); 15,218 MiB
  free of 16,311 MiB VRAM. This is above the general 10% runtime reserve but
  below fit-03's 25% start gate. No model job was admitted.
- Storage documentation reservation:
  `WRENCH-CONTEXT-PRUNING-RESEARCH-REFRESH-20260927-01`, 300,000 bytes. Final
  accounting before release reported `WITHIN_LIMIT`: 10,991,259,351 actual
  bytes plus 6,403,000 active reserved bytes, or 10,997,662,351 projected
  bytes against the 50,000,000,000-byte ceiling. The inventory included the
  repository, approved Wrench data root, all listed Wrench paths, and
  `C:\Users\stanc\github\subroute`. This job reservation remains active
  through closeout and is released only after the final files are accounted
  for.

## Sources

- [SWE-Pruner, arXiv:2601.16746](https://arxiv.org/abs/2601.16746)
- [Paritok-4B, arXiv:2608.24188](https://arxiv.org/abs/2608.24188)
- [SWE-Pruner Pro, arXiv:2607.18213](https://arxiv.org/abs/2607.18213)
- [ACON, arXiv:2510.00615](https://arxiv.org/abs/2510.00615)
