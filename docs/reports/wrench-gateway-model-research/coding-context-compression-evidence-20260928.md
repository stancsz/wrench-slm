# Coding-context compression evidence addendum

Date: 2026-09-28 (America/Edmonton)

Status: literature synthesis; no model, benchmark, or provider completion was run

Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)

## Decision

The strongest directly relevant result found is SWEzze: a Qwen3-Reranker-0.6B
with LoRA trained to keep issue-relevant code segments. It is evidence that a
small model can do a narrow context-selection job in front of a stronger code
model. It is not evidence that the small model can implement repository tasks
or sustain an engineering workday.

On the paper's 500 SWE-bench Verified tasks, SWEzze reduced total repair-step
tokens by 51.8% to 71.3% across three downstream models and increased resolved
instances by 2.0 to 4.6 percentage points versus no compression. These are
strong results for context pruning, but they fall short of Wrench's 95% token
and 95% all-in dollar targets. Compression alone cannot support the 95/95
claim. Reaching it would require a measured share of tasks to finish locally,
plus savings from deterministic mechanics and very low-cost fallback use.

Keep the current bounded Fit-03 package unchanged. Its synthetic controller
screen is not a SWEzze-style segment-ranker evaluation, a local coding-worker
evaluation, or a product utility result. If the owner later expands the
experiment, compare an oracle-supervised structural segment selector with
deterministic selection and the current controller as a separate stage.
This is consistent with Wrench's own evidence: the earlier broad 0.8B
semantic-controller direction was closed after a failed screen, and the
deterministic prototype's 11.64% reduction was synthetic input-token reduction
only, not complete-session frontier savings.

## Closest match: SWEzze

The authors fine-tune Qwen3-Reranker-0.6B with LoRA rank 16 and alpha 32. The
model scores AST-derived file, function, and statement-block segments for
retention; deterministic code performs segmentation and budget-aware context
assembly. The training signal is execution-based: the authors use search and
delta debugging to find contexts where a stronger repair model generates a
patch that passes tests, then label the retained segments. They report 3,157
instances from 41 Python repositories in the distilled corpus, with the
distillation oracle using Qwen3-Coder-30B. This is a concrete precedent for a
small learned selector plus deterministic mechanics, and for labels grounded
in successful outcomes rather than similarity alone.

On the 500 issue set spanning 12 Python repositories, the paper reports:

| Downstream repair model | No-compression resolved | SWEzze resolved | Total repair-token reduction |
|---|---:|---:|---:|
| DeepSeek-V3.2 | 47.8% | 52.2% | 55.9% |
| Qwen3-Coder-Next | 40.0% | 42.0% | 51.8% |
| GPT-5.2 | 53.2% | 57.8% | 71.3% |

The token totals include prompt and completion tokens in the repair step. The
paper separately reports 2.5 to 10 seconds of compressor latency per task
across its backends. It does not establish Wrench's complete session costs,
provider bills, local energy and hardware cost, retries, human rescue, broad
repository coverage, or eight-hour operation. It is an arXiv paper, not an
independent Wrench replication. Its SWE-bench evaluation also inherits the
benchmark-quality limits already recorded in the North Star.

The method has an important design lesson: train for sufficient context, not
maximum deletion. The study reports that overly aggressive compressors can
remove the code ingredients needed to produce a passing patch. Preserve
original spans, exact source identity, and a recovery path. Make uncertainty
retain more context or abstain.

## Separate result: local KV-cache compression

CodeComp adds Joern-derived code-structure signals to KV-cache pruning,
protecting items such as call sites, branches, assignments, and return values.
The authors report better code-generation and localization results than
attention-only KV pruning at equal memory budgets, including matching the
uncompressed patch quality on their reported test. This supports structure-aware
retention when a local model serves a long context. KV-cache pruning does not
remove provider-billed prompt tokens, so it cannot be counted as SubRoute or
frontier-token savings. It is a separate local-serving optimization and would
need its own runtime compatibility and hardware test.

## Wrench experiment implication

1. Keep exact mechanics deterministic: parse tool schemas, enforce allowed
   namespaces, count tokens, retrieve source spans, remove duplicate or stale
   material, preserve originals, and verify bounded output.
2. Use LoRA only for a bounded decision where the learned score can improve
   evidence selection. A 0.6B to 0.8B model is credible for ranking or route
   proposals; the published evidence does not justify treating it as the
   repository engineer.
3. Compare a deterministic selector, the current Wrench controller, and any
   separately admitted segment-ranker on identical tasks. Validate task
   outcomes by tests and include compression overhead, local resources,
   retries, fallback, and rescue in the ledger.
4. Keep hosted fallback as the difficult-task path. At SubRoute `127.0.0.1:4000`,
   today's GET-only check reports the active alias `openrouter`, forced mode,
   and policy version 4. This confirms the local control plane only. It does
   not establish the upstream model, a completion, tool-call quality, or a
   bill. No completion was sent because the aggregate USD cap is still absent.
5. Do not infer 95% token savings from 95% local episode completion. The 5%
   escalated episodes can dominate tokens if they are much harder. Measure
   savings against the paired frontier-only token denominator.

This evidence strengthens the case for a small LoRA context selector and
lossless deterministic recovery. It does not change the current candidate,
Fit-03 gates, data boundary, route, or product claim.

## Under-10B model and LoRA fit

The owner removed the earlier preference for the smallest model. The choice
should therefore be made by role and measured hardware fit, not by parameter
count alone. Keep the context controller and the code-writing worker as
separate roles in evaluation: Wrench's learned controller makes bounded
context and route proposals, while a coding worker handles implementation and
tests. A worker may be evaluated at a larger size without replacing the
controller's current Fit-03 identity.

| Candidate | Public coding/tool signal | Published LoRA or memory signal | Wrench disposition |
|---|---|---|---|
| Qwen3.5-4B | Qwen reports 55.8 LiveCodeBench v6 and 50.3 BFCL-V4; the model card documents the `qwen3_coder` tool-call parser | Unsloth reports about 10 GB VRAM for BF16 LoRA; its guide discourages QLoRA on Qwen3.5 | Best first larger candidate to evaluate on this RTX 5060 Ti. It is already present as a Q4 Ollama tag, but remains outside Wrench storage accounting and unreachable through the current SubRoute `desktop` alias. |
| Qwen3.5-9B | Qwen reports 65.6 LiveCodeBench v6 and 66.1 BFCL-V4 | Unsloth reports about 22 GB VRAM for BF16 LoRA, above this GPU's 16,311 MiB capacity; its inference table lists about 6.5 GB total memory for a 4-bit model | Plausible quantized inference challenger if the 4B worker fails quality, but not the first LoRA-training candidate on this GPU. It would need its own exact inventory and local sustained-run test. |
| Gemma 4 E4B | Google reports 52.0 LiveCodeBench v6, native function calling, and 128K context; the model has 4.5B effective parameters and 8B total including embeddings | Google's official tuning docs include LoRA/PEFT paths, but the cited model card does not establish this host's fine-tuning footprint | Useful second-family challenger if Qwen's runtime or tool-call path fails. Its total parameter count and exact quantized footprint need admission before any download. |

These vendor or framework figures are screening evidence, not Wrench results.
Unsloth's VRAM estimates are not a guarantee for this exact 5060 Ti, software
stack, sequence length, batch size, or concurrent system load. The 4B BF16
LoRA estimate is below nominal GPU capacity, but training is not admitted at
the current 11.58% free system RAM snapshot; retain the 10% RAM and VRAM floors
throughout any run. Run a short, exact-identity compatibility and resource
preflight before a bounded fit. Measure the actual minimum free RAM/VRAM,
tokens per second, prefill latency, OOM/recovery behavior, and adapter
save/load parity under the intended context size.

Qwen3.5-4B is a candidate recommendation, not a conclusion that it runs
smoothly. Its official card calls out version-sensitive SGLang/vLLM setup and
a Qwen3 tool parser; Wrench still needs an end-to-end tool-call round trip
through its intended local integration. Do not change or restart SubRoute to
make that route work. The existing local 4B tag and SubRoute control-plane
health do not prove a usable local coding agent.

## Primary sources

- Jia, Barr, and Mechtaev, [Compressing Code Context for LLM-based Issue Resolution (SWEzze)](https://arxiv.org/abs/2603.28119), arXiv:2603.28119, 2026.
- Chen et al., [CodeComp: Structural KV Cache Compression for Agentic Coding](https://arxiv.org/abs/2604.10235), arXiv:2604.10235, 2026.
- He, Wang, and Chen, [CodePromptZip: Code-specific Prompt Compression for Retrieval-Augmented Generation in Coding Tasks with LMs](https://arxiv.org/abs/2502.14925), arXiv:2502.14925, 2025. This is supporting evidence for trained code-example compressors with copy mechanisms; its RAG code-generation tasks are a less direct match than issue resolution.
- [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B) and [Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B), Apache 2.0, including official benchmark tables and serving guidance.
- [Unsloth Qwen3.5 LoRA and inference guide](https://unsloth.ai/docs/models/qwen3.5/fine-tune), a third-party framework's model-specific memory estimates and QLoRA caveat.
- [Google Gemma 4 model card](https://ai.google.dev/gemma/docs/core/model_card_4) and [official Gemma fine-tuning guide](https://ai.google.dev/gemma/docs/tune), including E4B size, coding, tool, and LoRA details.
