# Wrench small-model gateway research synthesis

Date: 2026-09-27  
Status: research decision, not an effectiveness result  
Scope: small LoRA gateway, deterministic context mechanics, cost and sustained engineering

## Decision

Treat Wrench as a deterministic context runtime with a small, trained proposal
model, not as a small autonomous software engineer. Keep the stronger coding
model responsible for open-ended diagnosis, architecture, multi-file edits,
and recovery from ambiguous failures. The existing SubRoute at
`http://127.0.0.1:4000` is the specified comparison/teacher path, but its
generation arm remains closed until a numeric aggregate spend cap and working
hard cost and receipt checks are in place.

The most plausible product path is:

1. **No model for exact work.** Deterministic code should filter validated
   tool schemas, count tokens, search and retrieve exact source, assemble
   source-linked context, preserve originals, and validate proposals.
2. **A Wrench-specific LoRA for bounded choices.** Start with the already
   staged Qwen3.5-0.8B only for finite decisions such as ranking source-backed
   lines, selecting a compaction policy, retrieving an omitted source span, or
   abstaining. Keep the output to a strict schema. This is distinct from the
   failed 0/10 general semantic-controller screen.
3. **Qwen3.5-2B as the first capacity challenger.** Test it only if a frozen
   0.8B result exhibits a named and measurable capacity failure. Its vendor
   card shows a substantial 0.8B-to-2B gap on BFCL-V4 (25.3 to 43.6),
   TAU2-Bench (11.6 to 48.8), and LongBench v2 (26.1 to 38.7), but these are
   not coding-agent or Wrench outcomes. Its published weight tree is about
   4.57 GB before cache and runtime copies, so it needs a fresh pinned
   inventory and job admission.
4. **Keep 4B as a later, separately admitted research candidate.** The
   strongest direct small-model coding-context analogue, Paritok-4B, is a
   Qwen3-4B LoRA, not a Qwen3.5-4B Wrench result. Its paper targets one
   24-GB GPU. Do not assume it fits or transfers to this 16-GB host.
5. **Do not assign all-day coding to the gateway SLM.** Measure that as a
   separate, paired workflow with a tool-capable coding model and real
   repository outcomes. Public small-model benchmarks and short synthetic
   decisions do not establish sustained engineering.

The complete comparative survey and candidate inventories remain in the
[2026-09-27 research report](research-20260927.md). This synthesis applies
newer context-cost evidence and narrows the next experiment.

## What the newer evidence changes

| Evidence | What it supports | What it does not support |
| --- | --- | --- |
| [SWE-Pruner](https://arxiv.org/abs/2601.16746), 0.6B task-aware line skimmer | A very small learned model can select code lines by current task intent. The authors report 23%-54% token reduction on multi-turn agent tasks; one reported SWE-Bench Verified comparison is 64% solved versus 62% baseline with 31% fewer tokens. | It is a specialized Qwen3-Reranker/CRF architecture, not a Wrench LoRA. The measured savings are far below 95%; the long single-turn compression result is not multi-turn proof. This is an arXiv preprint. |
| [Paritok-4B](https://arxiv.org/abs/2608.24188), a Qwen3-4B LoRA | Intent-conditioned, extractive line selection is a credible coding-context approach. On 300 SWE-bench Lite cases it retained 25.7% of context and 86.5% of uncompressed single-shot solve quality. With the line-numbered format it retained 27.8% of context and 89.3% of quality. | This does not establish 95% quality retention or agent-loop cost savings. Its own analysis says the 300-case quality interval is broad; failure to detect a paired difference (McNemar p=0.079) is not a non-inferiority proof. It uses a 24-GB GPU target and is not Wrench or Qwen3.5 evidence. |
| [Empirical cost attribution of context-compression gateways](https://arxiv.org/abs/2609.22114), submitted 2026-08-19 | In the authors' instrumented Claude Code/Codex sessions, filtering tool schemas removed a reported 21K-57K tokens per typical turn. File-read compression saved about 2% of the cache-priced prefix immediately, then accumulated across repeated multi-turn history; restoring exact originals bounded the cost of recovering omitted text. | This is an early preprint by the Paritok authors on their particular gateway and agent stack. Its token quantities cannot be assumed for Wrench. It reinforces measuring actual request payloads, cache billing, tool schemas, recall, and complete sessions instead of multiplying a one-shot compression ratio into a savings claim. |
| [Qwen3.5-2B model card](https://huggingface.co/Qwen/Qwen3.5-2B) | A plausible intermediate controller size; Qwen explicitly lists prototyping and task-specific fine-tuning as intended uses. | Benchmarks are vendor-reported, and neither BFCL nor LongBench proves repo coding, all-day operation, Wrench quality, or 95% savings. |

The practical lesson is to measure the *cost composition* before training for
compression. First measure repeated tool-schema tokens, repeated histories,
file reads, cache-hit/miss pricing, local work, and recovery. A deterministic
allowlist for tools the agent is actually authorized to use may beat an SLM
on cost and latency. Test it as a separate arm and preserve every required
tool; do not strip schemas merely to make token counts look good.

## Model-role boundary

| Component | Wrench responsibility | Appropriate model size |
| --- | --- | --- |
| Mechanical runtime | Exact parsing, token accounting, allowlisted tool-schema filtering, indexing/search, source IDs/hashes, assembly, retrieval, validation, receipts, rollback | No generative model |
| Context/route proposer | Rank known source spans; choose bounded retrieve/compact/stop/abstain action; propose local or frontier route | 0.8B first; 2B only after a measured capacity error |
| Coding worker | Plan and implement semantic changes, repair tests, review diffs, resolve multi-step failures | A separately evaluated code model, likely larger than the controller; current SubRoute's forced OpenRouter/MiniMax M3 route has not been established as tool-capable |
| Frontier fallback | Difficult or uncertain coding work with explicit task accounting | Use the pinned route only after cap and receipt gates pass |

The model proposes; host code checks the schema, source identity, policy,
budget, and permission boundary. Use extractive spans with exact provenance
and on-demand original-text recovery before trying abstractive summaries.
Learning should improve selection decisions from reviewed outcomes; mutable
code facts and current repository state remain external state.

## The 95% claims need stricter accounting

Keep these as separate acceptance metrics: paired verified success retention,
frontier episode rate, frontier-token savings, all-in dollar savings, local
completion, and sustained-work reliability. A 5% *episode* escalation rate
does not mean 5% of baseline spend: the escalated tasks may be much harder and
use more tokens. Nor does 95% frontier-token reduction prove 95% lower all-in
cost.

If baseline cost is `C`, the literal 95%-cheaper target requires
`local_inference + energy + hardware/runtime allocation + training/evaluation
amortization + labor + frontier_cost <= 0.05*C`. Any local operating cost
uses part of that 5% allowance. The frontier share must therefore be below
5% whenever local costs are nonzero. Count retries, tool schemas, verification,
compaction, cache misses, and re-fetches. Keep all failed tasks and human
rescues in the denominator and report paired uncertainty bounds.

The current proof protocol correctly sets a much higher bar than a synthetic
route screen: powered paired tasks, grouped/time-isolated final data,
provider-authoritative usage/cost receipts, and independent multi-hour
repository sessions. Preserve that protocol; do not weaken the threshold to
match published compression numbers.

## Current Wrench gates

- Latest live RAM sample in this iteration: 3.89 / 31.94 GiB free (about
  12.2%). This is below fit-03's 25% free-RAM start gate. GPU memory was not
  sampled in this iteration. No training, model load, inference, or benchmark
  was admitted.
- The exact Qwen3.5-0.8B snapshot and screen-01 inventory have a preparation
  review, but the run-specific admission is absent. No adapter exists; the
  prior full-fit attempt stopped before its first optimizer update.
- SubRoute `:4000` is the specified read-only route. Its force alias maps to
  OpenRouter/MiniMax M3, while the actual provider and bill require a
  generation receipt. The public proxy path for outbound controls and
  per-call receipts remains unproven; no paid call is authorized without a
  numeric aggregate cap and hard fail-closed accounting.
- Existing E0 context and teacher-arm focused checks validate selected
  deterministic and accounting behavior. They are not model-effectiveness,
  task-success, savings, or all-day engineering evidence.
- The presently authorized synthetic screens are mechanics diagnostics, not a
  representative corpus of repository coding trajectories or proof of
  generalization to a workday.

## Recommended decision sequence

1. Measure baseline request composition from a no-spend, privacy-reviewed
   trace: tool schemas, history, file/tool output, cache billing, retries,
   and local context rebuilding. Use controlled fixtures first.
2. Add and verify deterministic, capability-aware schema filtering and exact
   source-span recovery as independently measurable mechanics.
3. Complete the admitted synthetic-only 0.8B LoRA candidate when all RAM,
   VRAM, storage, provenance, and scorer gates pass. Compare deterministic,
   frozen 0.8B, and Wrench LoRA on the same frozen held-out mechanics data.
4. If and only if the held-out result shows a specific capacity failure, pin
   and inventory 2B and prepare a separate runtime/LoRA/resource admission.
5. Once the owner supplies an aggregate USD cap and the SubRoute proxy path
   proves cost controls and complete receipts through a mock upstream, run the
   capped frontier comparison. Do not infer real-provider costs from catalog
   prices or `:4000` health metadata.
6. Evaluate real engineering only with approved task data, a tool-capable
   coding baseline, independent outcome verification, and the predeclared
   multi-session protocol.

## Research sources

- [SWE-Pruner, arXiv:2601.16746](https://arxiv.org/abs/2601.16746)
- [Paritok-4B, arXiv:2608.24188](https://arxiv.org/abs/2608.24188)
- [Empirical cost attribution, arXiv:2609.22114](https://arxiv.org/abs/2609.22114)
- [Qwen3.5-2B model card](https://huggingface.co/Qwen/Qwen3.5-2B)
- [Wrench product proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md)
- [SubRoute route and integration evidence, iteration 015](../../evals/wrench-gateway-model-research/iteration-015-subroute-mock-boundary-20260927.md)
- [Current fit/admission evidence, iteration 024](../../evals/wrench-gateway-model-research/iteration-024-hourly-execution-priority-20260927.md)
