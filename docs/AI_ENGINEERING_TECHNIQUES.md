# AI engineering techniques and where Wrench fits

Assessment date: 2026-09-09. This is a source-level assessment of the current working tree, not a fresh hardware benchmark or release certification. Existing progress documents are recorded evidence, not a live process-status check.

Wrench can directly apply model adaptation, cached generation, efficient attention, and structured tool prediction. It can integrate serving optimizations through an inference backend. Its most distinctive research direction is tool-level speculation, whose usefulness still requires an end-to-end comparison. Building a distributed inference engine is a poor fit for the current small-model, single-device goal.

The active [goal](../goal.md) prioritizes validated standalone weights. Router integration and cloud savings are deferred. This guide does not change that priority or authorize new training, deployment, or gateway changes.

## Concepts and coverage

Prefill processes the input prompt; decode generates subsequent tokens. KV caching saves attention keys and values so decoding can reuse prior work. Faster prefill, faster decode, higher throughput, and lower memory consumption are separate outcomes.

In this table, **present** means the inspected path uses the mechanism, **partial** means related code exists with important limits, **candidate** means a plausible integration without demonstrated benefit here, and **defer** means outside the current priority.

| Technique | Mechanism and purpose | Wrench coverage and assessment |
| --- | --- | --- |
| Per-request KV caching | Reuse prior attention keys and values during generation rather than recomputing the full prefix. | **Present in Pro.** `PilotExecutor.predict` calls Hugging Face generation with `use_cache=True`. The native `NanoWrench.generate` instead forwards all accumulated tokens each step; its header's cache claim is not implemented in that loop. Keep these paths distinct. |
| FlashAttention / SDPA | Attention tiling reduces GPU memory traffic without approximating the attention calculation. SDPA is an API that can select different kernels. | **Partial.** Pro loading and training request `attn_implementation='sdpa'`; the native model calls PyTorch SDPA. This does not establish that a FlashAttention kernel actually ran. Profile kernel selection and full-call latency before claiming acceleration. |
| PagedAttention | Allocate KV states in blocks to reduce cache fragmentation and support more concurrent sequences. | **Candidate, later.** No paged-cache manager was found in the inspected Wrench paths. Integrate an established serving backend if concurrency creates memory pressure; do not build one for a single-request pilot. |
| Continuous batching | Admit and retire requests while other requests continue decoding. | **Candidate, later.** The pilot predicts one record per call. Training minibatches and a threaded HTTP server are not continuous inference batching. Useful only after measuring a concurrent serving workload. |
| Prefix caching | Reuse KV states across requests with an identical initial token sequence. | **Candidate.** Repeated tool definitions and instructions could benefit. Current per-request caching does not provide this. Measure actual common prefixes; key caches by model/adapter, tokenizer, and exact input, with appropriate isolation. Never confuse KV reuse with reusing possibly stale tool results. |
| Chunked prefill | Split long prompt processing into chunks and interleave it with decoding requests. | **Candidate, lower priority.** Helps mixed long/short concurrent traffic. The pilot currently bounds input length and uses serial prediction. Integrate through a scheduler only if that workload emerges. |
| Weight quantization | Reduce weight precision to lower memory use, potentially improving speed with suitable kernels. | **Candidate, strong fit after quality gates.** Current Pro loading uses BF16 on CUDA and FP32 on CPU, not INT4/INT8. Quantized export is especially relevant to the intended Flash CPU tier, but no measured Flash footprint or speed is established here. Re-evaluate tool names, literal strings, quoting, and numerical boundaries after conversion. |
| KV-cache quantization | Store attention states at lower precision to reduce cache memory. | **Candidate, conditional.** No quantized cache is configured. Prioritize only if long contexts or concurrency make the cache material. Dequantization overhead can make short requests slower. |
| Prefill/decode disaggregation | Put prompt processing and generation on separate serving instances and transfer KV states. | **Defer.** No such runtime is present. Adds transfer and orchestration costs that do not match the current standalone 0.5B, single-device objective. |
| Tensor parallelism | Split model operations across GPUs, exchanging intermediate results. | **Defer.** Current Pro training/loading targets one CUDA device. Communication complexity is hard to justify for this model size and intended hardware. |
| Knowledge distillation | Train a student on teacher behavior, such as generated targets or probability distributions. | **Partial.** `fetch_real_data.py` generates teacher-authored prompt variants while preserving seed targets. This is data augmentation, not teacher-logit matching or evidence of frontier-level capability transfer. Quality-checked teacher tool-call targets are a reasonable future extension with provenance and family-isolated evaluation. |
| LoRA / QLoRA | Train small low-rank adapters; QLoRA also uses a quantized base to save training memory. | **LoRA present; QLoRA candidate.** `pilot_train.py` uses rank-16 PEFT adapters on a BF16 base. Do not call this QLoRA. Existing training receipts support completed adapter training, not release readiness. Use QLoRA only if training memory becomes a bottleneck worth the additional dependencies. |
| Token-level speculative decoding | A cheap draft proposes several tokens; a target model verifies them in a block. Appropriate acceptance/correction preserves the target sampling distribution. | **Research candidate, not implemented.** No target verification/acceptance loop is present. Wrench could be a tool-specialized draft model for a controllable target runtime, subject to tokenization compatibility or an explicit cross-tokenizer method. A normal cloud chat call that reviews JSON is not this algorithm. |

See the primary references below for algorithm definitions. Status judgments above come from the repository paths listed in the evidence section.

## Wrench-specific adjacent techniques

**Tool pre-execution and draft verification are the strongest architectural fit.** In `pilot_workflow.run_episode`, the local model or rules predict a complete call, the disposable environment executes permitted reads or records a write draft, and the observation is supplied to the cloud model. The current code does this before the cloud call, not concurrently while the cloud model is thinking. It therefore demonstrates the workflow structure, not overlap of cloud and local execution. The interrupted comparison recorded in [pilot progress](USEFULNESS_PILOT_PROGRESS.md) does not establish net latency or token savings.

**Grammar-constrained decoding is relevant but path-dependent.** `fsm.py`, `tokenizer_fsm.py`, and `inference.py` contain grammar machinery. The current packaged Pro path uses `PilotExecutor`, which explicitly generates without grammar constraints and then validates the output. Rejected output remains an invalid prediction even when converted to `ROUTER_FALLBACK`. Integrating constraints with the actual pretrained tokenizer is useful future work, but syntactic validity alone cannot guarantee correct paths, arguments, or task outcomes.

**Selective fallback is part of the current contract.** A model can abstain, and invalid output is rejected at the boundary. This supports a future local/cloud cascade, but it does not prove calibrated confidence, optimal routing, or a particular offload rate. Evaluate useful coverage and incorrect accepted calls together. Gateway routing work stays deferred under the active goal.

**Multi-token prediction is a separate research extension.** The README proposes extra prediction heads. The inspected native model has a single language-model output head and an autoregressive generation loop. No implemented MTP training and verified multi-token decoding path supports the advertised throughput figures.

## Future harness and gateway reference

Direction recorded on 2026-09-09: Wrench may expand into harness and gateway work around the model family. Keep the techniques in this document as future design references, including those deferred from the standalone model goal. This is an exploratory direction, not a commitment to implement every technique or a change to the current release requirements.

The following allocation is a proposed division of responsibilities, not a description of shipped components:

| Layer | Potential responsibilities | Techniques it could cover |
| --- | --- | --- |
| Model and training | Learn tool selection and exact arguments; produce versioned, independently evaluated weights. | LoRA/QLoRA, teacher-student distillation, quantized artifacts, possible MTP or draft-model training. |
| Inference backend | Load weights and execute token generation efficiently; expose supported capabilities and measurements. | KV caching, SDPA/FlashAttention, grammar constraints, prefix caching, cache quantization, continuous batching, PagedAttention, chunked prefill, token-level speculative decoding. |
| Harness | Manage the request-to-tool workflow, validate proposals, execute permitted tools, supply observations, and evaluate final outcomes. | Tool pre-execution, draft verification, bounded retries, correction handling, controlled local/cloud overlap, and matched workflow experiments. |
| Gateway | Select local or upstream execution, enforce budgets, propagate cancellation, and correlate usage and latency across calls. | Selective fallback and model cascades, backend selection, cache-aware routing, concurrency admission, and future routing to distributed serving backends. |

A gateway can select or configure a backend without implementing its attention kernels. Likewise, a harness can submit a complete tool draft for review without implementing token-level speculative decoding. Keep these distinctions explicit in future plans and capability claims.

Potential work packages to revisit:

1. **Shared request and observation contract.** Carry request IDs, model/adapter identity, proposed tool arguments, validation outcomes, execution results, and timing through the model, harness, and gateway. Preserve the distinction between a proposal, an executed read, and an unexecuted write draft.
2. **Speculation lifecycle.** Explore overlapping local prediction with an upstream request, with bounded speculative work, cancellation, duplicate suppression, observation freshness, and explicit handling of rejected or unused results. Count wasted work as well as avoided turns. Do not assume idempotency alone makes an operation suitable for speculative execution.
3. **Routing and budget policy.** Compare rules-only, model-assisted, and cloud-only paths using declared routing conditions. Record the actual provider/model, fallback reason, retries, and complete usage rather than inferring savings from the requested route.
4. **Backend capability adapter.** Expose which optimizations a backend actually supports and enables. Start with the current standalone path; consider serving engines when workload evidence warrants them. Keep token verification inside a backend that exposes the required target-model operations.
5. **Cache policy.** Separate model KV-prefix reuse from tool-result caching. For tool results, define freshness, invalidation, argument/environment identity, and access scope before reuse. Measure hit rates and incorrect or stale reuse independently.
6. **Replay and comparison harness.** Preserve reproducible scenarios, independent evaluation families, actual tool outcomes, and complete cost/latency traces. Evaluate cold and warm caches, concurrency, timeouts, failed speculation, and fallback cases against a baseline.

When one of these becomes active work, create a bounded implementation plan with its workload, ownership, baseline, success criteria, and required backend capabilities. The present assessment remains a reference; the active goal and frozen evaluation protocols continue to govern current work.

## Recommended order

1. **Finish model correctness and standalone release validation.** Preserve independent evaluation, literal argument accuracy, actual disposable-tool outcomes, and clean loading. LoRA is already the practical adaptation method; additional techniques do not substitute for these gates.
2. **Measure the existing inference path.** Use the pinned model, adapter, tokenizer, prompts, and output budget. Separate cold loading from warm requests. Record hardware/software versions, attention kernel, full-call latency, output length, memory, and quality. Instrument TTFT and token intervals explicitly; the current pilot's total duration does not provide them.
3. **Try weight quantization and profile SDPA.** Compare each change against the same baseline and all release quality gates. Confirm CPU backend compatibility for a Flash experiment. Include peak process memory, GPU allocated/reserved memory, and system device usage with their distinct scopes.
4. **Integrate constrained generation if malformed output remains material.** Measure both schema validity and exact arguments, including mask overhead and truncated output. Preserve raw failure accounting.
5. **After the model goal, test prefix reuse and tool-level speculation.** Prefix caching needs repeat-prefix traffic. Tool speculation needs a complete matched workflow comparison that includes local prediction, tool execution, cloud verification, corrections, and fallback costs. Resolve the interrupted protocol's routing condition before resuming it.
6. **Add serving or drafting infrastructure only when justified.** Continuous batching, paged caches, and chunked prefill require a concurrent workload. Token-level speculation requires a target engine and acceptance telemetry. Multi-GPU distribution is not a near-term requirement.

For every experiment, change one mechanism at a time. Report p50/p95/p99 with sample counts, throughput at stated concurrency, input/output lengths, peak memory, raw validity, exact tool/argument accuracy, real task success, and fallback coverage. Include failed requests and warm-up policy. For token speculation additionally measure accepted draft tokens, draft/verification overhead, and target-only baseline speed; for tool speculation measure avoided turns and total cost rather than token acceptance.

## Existing claims that must remain unverified

README section 7 contains an 85-95% token acceptance claim, a 2-3x speculative speedup, and 300+ tokens/second MTP throughput. The inspected implementation does not substantiate these numbers. Likewise, SDPA configuration is not kernel-level proof, grammar code in another path is not a guarantee for packaged Pro, and the interrupted pilot is not a successful cloud-savings comparison. Treat those statements as research aspirations, not measured capabilities. No new performance claim is made by this assessment.

## Repository evidence

- [Pro inference](../wrench/pilot_inference.py): cached greedy generation, input budget, raw-output validation, fallback accounting.
- [Packaged inference](../wrench/weight_inference.py): SDPA, dtype selection, pinned base and PEFT loading.
- [Training entry point](../scripts/pilot_train.py) and [SFT implementation](../wrench/sft.py): BF16 LoRA setup and supervised training.
- [Native model](../wrench/model.py): SDPA attention and full-prefix autoregressive loop.
- [Teacher data acquisition](../scripts/fetch_real_data.py): prompt-variant generation and provenance labels.
- [Workflow](../wrench/pilot_workflow.py) and [environment](../wrench/pilot_environment.py): preliminary observations, disposable tools, draft-only writes.
- [Grammar wrapper](../wrench/inference.py), [FSM](../wrench/fsm.py), and [tokenizer grammar](../wrench/tokenizer_fsm.py): separate constrained-generation machinery.
- [Model release progress](MODEL_RELEASE_PROGRESS.md) and [pilot progress](USEFULNESS_PILOT_PROGRESS.md): recorded training and comparison limits. Consult actual receipts before reusing point-in-time metrics.

## Primary references

- [FlashAttention paper](https://arxiv.org/abs/2205.14135): IO-aware exact attention.
- [PagedAttention paper](https://arxiv.org/abs/2309.06180): block-based KV memory management.
- [vLLM serving architecture](https://vllm-project.github.io/2025/09/05/anatomy-of-vllm.html): continuous batching, prefix reuse, chunked prefill, and serving internals.
- [vLLM disaggregated prefill](https://docs.vllm.ai/en/latest/features/disagg_prefill/): separate prefill and decode instances.
- [NVIDIA inference optimization](https://developer.nvidia.com/blog/?p=73739): quantization, parallelism, and speculative inference.
- [Hugging Face KV-cache strategies](https://huggingface.co/docs/transformers/v4.53.0/en/kv_cache): cache choices and quantization tradeoffs; this is versioned documentation, not a claim about installed dependencies.
- [Knowledge distillation paper](https://arxiv.org/abs/1503.02531): teacher-student knowledge transfer.
- [Hugging Face PEFT](https://huggingface.co/docs/peft/en/index): adapter training and quantization integrations.
