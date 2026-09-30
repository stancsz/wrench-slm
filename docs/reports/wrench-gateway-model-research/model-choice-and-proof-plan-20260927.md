# Wrench small-model choice and proof plan

Date: 2026-09-27 (America/Edmonton)
Status: research decision for the next candidate preflight; no model was downloaded, loaded, trained, or benchmarked
Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)

## Recommendation

Keep the product split into three jobs:

1. **Deterministic context runtime:** search, exact source retrieval, token
   counting, capability-aware tool-schema filtering, source-linked extractive
   compaction, original-text recovery, validation, and receipts. These
   mechanical operations do not need a language model.
2. **Wrench controller LoRA:** train a model for bounded proposals such as
   evidence rank, fetch-span, compact, stop, route, or abstain. The host checks
   every proposal. The adapter does not get shell, code-mutation, credential,
   or permission authority.
3. **Coding worker:** a separate local code model can take routine, well-scoped
   engineering tasks; the stronger model behind SubRoute handles uncertain or
   high-cost cases. A controller score is not a coding-worker score.

For the next **local coding-worker preflight**, use pinned Qwen3.5-4B first.
It is the smallest currently inventoried worker candidate in this comparison
with recent public coding and tool-use signals, it shares the family already
used by Wrench, and an external fine-tuning guide estimates BF16 LoRA at about
10 GB VRAM. Those points make it the best first fit experiment, not a winner:
that memory number is not a measurement on this RTX 5060 Ti, and no Wrench
repository task has been run on it.

Keep Qwen2.5-Coder-7B-Instruct as the **code-specialist challenger** if the
4B worker fails a named, predeclared coding-quality gate. Its dedicated code
training and conventional Qwen2 architecture are attractive, but its recent
local QLoRA fit, tool loop, latency, and sustained work are all unknown. It
also requires a new trainer/runtime path. Do not infer that “Coder” means
better repo-agent performance from the name alone.

For the learned Wrench controller, retain the already staged Qwen3.5-0.8B as
the lowest-cost LoRA control. A failed general semantic screen does not test
the trained finite-action policy. Promote the controller to Qwen3.5-2B only
after a frozen 0.8B LoRA evaluation shows a specific capacity error. This
keeps the controller small while testing coding generation as a separate
capability.

## Candidate inventory and fit evidence

| Role | Candidate and pinned identity | Current evidence | Disposition |
|---|---|---|---|
| Wrench controller baseline | Qwen3.5-0.8B, revision `2fc06364715b967f1860aea9cf38778875588b17`; local tree already inventoried | Existing trainer, attention-only targets, and one optimizer-step compatibility preflight. No finished adapter or held-out score. Untrained general semantic screen was 0/10. | First bounded Wrench-LoRA experiment after its live gates pass. Not a general coding agent. |
| Controller capacity challenger | Qwen3.5-2B, revision `15852e8c16360a2fea060d615a32b45270f8a8fc`; pinned tree 4,571,274,023 bytes | Squeez reports a Qwen3.5-2B LoRA with 92% tool-output token removal, 0.86 evidence recall, and 0.80 F1 on its own curated test. This is extraction, not Wrench task success; it misses 95% removal. | Advance only after a measured 0.8B capacity failure. |
| First local coding-worker preflight | Qwen3.5-4B, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; 14 files, 9,342,907,469 bytes | Model-card results: LiveCodeBench v6 55.8, BFCL-V4 50.3, TAU2-Bench 79.9. Unsloth estimates about 10 GB VRAM for BF16 LoRA and explicitly advises against QLoRA for Qwen3.5. No host fit or Wrench coding result. | First worker candidate to preflight, not a qualified model. Use BF16 LoRA only if the exact runtime path passes. |
| Code-specialist challenger | Qwen2.5-Coder-7B-Instruct, revision `c03e6d358207e414f1eca0bb1891e29f1db0e242`; 14 files, 15,242,807,397 bytes | 7.61B parameters; code-specific, Apache-2.0, Qwen2 causal model. Related Qwen-7B QLoRA profiles suggest short-context fit may be possible. No RTX 5060 Ti run. | Consider only if the 4B worker misses the frozen local-code gate. Candidate-specific QLoRA implementation and review are required. |

The Qwen3.5-4B inventory consists of `.gitattributes` (1,570 bytes),
`chat_template.jinja` (7,756), `config.json` (3,161), `LICENSE` (11,544),
`merges.txt` (3,353,259), the two weights shards (5,329,398,688 and
3,990,429,408), `model.safetensors.index.json` (76,196),
`preprocessor_config.json` (390), `README.md` (77,661),
`tokenizer_config.json` (16,710), `tokenizer.json` (12,807,982),
`video_preprocessor_config.json` (385), and `vocab.json` (6,722,759).
The two weight-shard SHA-256 values are
`26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61` and
`cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188`.
The inventory is metadata-only; no snapshot is present locally.

The 7B Coder inventory and four weight-shard hashes are in the
[candidate fit report](qwen25-coder-7b-fit-feasibility-20260927.md). A
conservative two-copy estimate for that model is about 41.49 GB of aggregate
Wrench storage once current data and reservations are included, leaving only
about 8.51 GB under the strict ceiling for runtime additions and outputs. The
4B two-copy estimate is about 29.68 GB including the present footprint and
reservations. Both remain below 50 GB on paper; any actual download or run
still needs a fresh reservation and destination-space check.

### Runtime compatibility

The current local runtime has Python 3.13.15, Torch 2.14.0+cu132,
Transformers 5.17.0, PEFT 0.21.0, and Accelerate 1.15.0. The existing Wrench
trainer is Qwen3.5-specific but loads FP32; it cannot be reused unchanged for
the 4B BF16 path. The installed environment does not contain bitsandbytes.
For the Qwen2.5-Coder 7B path, the official bitsandbytes install guide lists
Windows x86-64 CUDA 13.0-13.2 builds targeting `sm120`; the host GPU is an RTX
5060 Ti. That is library-target compatibility, not proof the wheel imports,
quantizes this model, or completes a training step on this machine. Its exact
package and dependency tree must be inventoried and reserved before install.

Qwen3.5's published 10 GB BF16-LoRA estimate is about 9,537 MiB. Against the
GPU's 16,311 MiB capacity that leaves about 6,774 MiB nominal headroom, before
runtime variance and the required 10% reserve. Qwen2.5-Coder QLoRA has less
margin and more integration work. These are prioritization calculations, not
resource admission.

### Bounded next fit preflight

When the machine is admitted again, the first 4B job should be a compatibility
preflight, not full training:

1. Require at least 25% system RAM free at start, and maintain at least 10%
   system RAM and VRAM free throughout. Recheck the exact storage reservation,
   destination free space, GPU identity, model tree, Python/Torch/Transformers/
   PEFT versions, and all output paths immediately before the job.
2. Use BF16 base weights with a LoRA adapter. Do not use QLoRA for this
   Qwen3.5 candidate because the current fine-tuning guide warns against it.
   Keep the exact model revision and original base/core state immutable.
3. Inspect the pinned 4B architecture's actual modules before setting the
   adapter targets. The 0.8B target count does not transfer automatically to
   the 4B architecture. Start with the reviewed attention-only profile only
   if the 4B projection map supports it; record the exact ordered target
   names and trainable parameter count in the receipt.
4. Run one optimizer step on authorized synthetic training rows only, with
   batch size 1 and sequence length 512. Record peak VRAM, minimum free RAM
   and VRAM, elapsed time, package/model identities, finite loss, and stop
   reason. Stop immediately if either 10% reserve is breached.
5. Do not read held-out data or retain/activate a candidate adapter in this
   preflight. After an exact-hash independent review, admit any longer
   synthetic fit as a separate job with its own reservation and stop rules.

This job cannot start at the current 7.98% free-RAM reading. If the 4B
preflight cannot retain the resource floor at 512 tokens, stop and compare a
smaller context or the 2B controller; do not silently move weights to an
unapproved volume or borrow the Coder-7B profile as fit evidence.

## What the present Wrench results do and do not show

- The base Qwen3.5-0.8B general semantic screen was 0/10. It did not test a
  Wrench-specific LoRA on a bounded controller schema.
- The one-step LoRA preflight proves one exact model/runtime/target setup can
  execute an optimizer step on synthetic rows. It did not retain a promoted
  adapter, establish learning, test held-out quality, or show coding ability.
- Deterministic E0 tests and token-accounting checks establish selected
  mechanics. The observed synthetic context reduction was about 12.1% over a
  handful of pairs, not 95% end-to-end frontier-token savings.
- The current 128-case synthetic split contains 81.25% LOCAL, 6.25% FRONTIER,
  and 12.5% ABSTAIN cases. Even a perfect classifier on that split cannot
  meet 95% local completion and a 5% frontier ceiling. It needs a new
  preregistered workload mix before it can test those claims.
- The 4B and 7B model-card results, published fine-tuning estimates, paper
  results, and static code review are research inputs. No local model has
  completed a Wrench held-out task set or an all-day coding study.

Therefore, the current result is **a failed unadapted general-controller
screen plus incomplete mechanics and fit evidence**. It does not establish
that every small model or a narrow Wrench LoRA fails. It also does not make
the 95% local / 95% token / 95%-cheaper target likely for arbitrary software
engineering. The credible testable bet is a narrow mechanical workload, with
the local coding worker evaluated separately.

## Evidence plan for an honest 95% claim

Freeze the population, task mix, repositories, time window, budgets, routes,
model and adapter hashes, retry policy, cache condition, success oracle, and
stopping rules before any confirmatory set opens. Keep tasks grouped by
repository, family, and time. The current synthetic seed stays mechanics-only.

Use paired arms on the same tasks:

1. Strong coding model alone.
2. Deterministic Wrench plus that same model.
3. Wrench-specific LoRA controller plus a local code worker and the same
   stronger model as bounded fallback.
4. If capacity requires it, the separately versioned controller or code
   worker candidate; never pool model identities.

For every planned episode, record verified completion, task quality, route
events, provider input/output/cached tokens, local tokens, retries,
verification, compaction and recovery calls, latency, local GPU/CPU time,
energy, human intervention, and cost. Failures, abstentions, timeouts, and
rescues stay in the denominator. Report these gates independently:

- At least 95% of all planned episodes complete locally, with the
  preregistered one-sided confidence bound passing 95%.
- At most 5% of all planned episodes make any frontier call, with its bound
  passing 5%.
- At least 95% of frontier-only verified task success is retained.
- `1 - hybrid_frontier_tokens / frontier_only_frontier_tokens` is at least
  95%, using paired token sums, including all remote retries, verification,
  cached input, compaction, and re-fetch calls.
- `1 - hybrid_all_in_cost / frontier_only_all_in_cost` is at least 95%,
  including provider bills, local compute and energy, runtime/hardware
  allocation, human rescue, and preregistered LoRA training/evaluation cost.
- A separate multi-session endurance study verifies work quality, recovery,
  and acceptable human rescue across repositories and languages.

A 5% routed-episode rate does not guarantee 95% token reduction; escalations
may contain most baseline token volume. Local context compression may reduce
the fallback prompt, but it earns credit only if exact-source recovery and
downstream task success hold. Existing research reports reductions mostly in
the 23%-54% range for coding-agent pruning; a 92% one-observation extraction
result is still below the requested 95% and is not a whole-session result.

## SubRoute and current admission

The specified route is the existing `http://127.0.0.1:4000`. This iteration's
read-only GET returned `I'm alive!` from `/health/liveliness`; `/models` listed
19 aliases. A prior saved snapshot identifies the forced `openrouter` alias
and the configured MiniMax M3 mapping. Neither GET identifies the upstream
provider that would process a paid generation or supplies a billing receipt.
The numeric aggregate spend cap and proven fail-closed caller accounting are
still absent, so the frontier comparison remains closed. No POST, generation,
or provider spend occurred.

At this iteration, free system RAM was 7.98%, below both the 10% operating
floor and the 25% training start gate. The storage checker including the
SubRoute checkout reported `WITHIN_LIMIT` at 10,992,599,173 actual bytes,
8,103,000 bytes of pre-existing reservations, and 500,000 bytes reserved for
this documentation job. No model, test, training, inference, benchmark, or
delegated job was admitted.

## Sources

- [Qwen3.5-4B model card and benchmark table](https://huggingface.co/Qwen/Qwen3.5-4B)
- [Pinned Qwen3.5-4B tree](https://huggingface.co/Qwen/Qwen3.5-4B/tree/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a)
- [Qwen2.5-Coder-7B model card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct)
- [Pinned Qwen2.5-Coder-7B tree](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/tree/c03e6d358207e414f1eca0bb1891e29f1db0e242)
- [Qwen3-Coder supported models and model-size list](https://github.com/QwenLM/Qwen3-Coder/blob/main/README.md)
- [Qwen3.5 BF16-LoRA memory and QLoRA guidance](https://unsloth.ai/docs/models/qwen3.5/fine-tune)
- [bitsandbytes Windows CUDA targets and system requirements](https://huggingface.co/docs/bitsandbytes/installation)
- [Squeez: task-conditioned tool-output extraction](https://arxiv.org/abs/2604.04979)
- [SWE-Pruner: task-aware coding-context selection](https://arxiv.org/abs/2601.16746)
- [Paritok-4B coding-context compression](https://arxiv.org/abs/2608.24188)
- [Existing Wrench paired proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md)
- [Existing Wrench research synthesis](research-synthesis-20260927.md)
