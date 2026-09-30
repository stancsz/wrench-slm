# Wrench gateway model decision reassessment

Date: 2026-09-27  
Status: research synthesis; no new model or provider run  
Question: what can a small Wrench LoRA realistically do while the combined system still supports sustained software engineering?

## Decision

Use a **deterministic context runtime, a narrow Wrench LoRA, and a separate capable coding worker**. Do not ask a sub-10B Wrench controller to be both the safe context gateway and a proven all-day software engineer. The available evidence does not support that combined claim.

The best supported small-model job is task-conditioned, extractive selection of source-backed evidence from tool output. Keep the original output in bounded local state so the coding worker can request the exact omitted span. Let deterministic code own tool authorization, schema filtering, token accounting, retrieval, provenance, context assembly, validation, and receipts. The LoRA proposes a finite action such as `KEEP`, `FETCH_SPAN`, `COMPACT_EXTRACTIVELY`, `ENOUGH`, or `ABSTAIN`; host code validates the proposal and never grants authority from model output.

### Model choice, separated by decision

| Decision | Recommendation | Evidence status |
| --- | --- | --- |
| Smallest staged Wrench feasibility candidate | Keep the already-inventoried Qwen3.5-0.8B as the first bounded Wrench LoRA experiment, if and when its exact run gates pass. It avoids a new base download and tests whether the narrow task works at the lowest model size. | The Wrench adapter does not exist yet. The general 0.8B screen was 0/10, the one-step attention-only preflight is compatibility evidence only, and no held-out quality score exists. |
| Best research-backed size for extractive tool-output pruning | Qwen3.5-2B is the strongest next challenger, not a replacement selected by benchmark reputation. A 2026 LoRA paper reports this exact family and scale for task-conditioned extraction. Advance only after the 0.8B result names a capacity failure, then pin and inventory all files and re-admit storage, runtime, and hardware. | The paper reports 0.86 evidence recall and 0.80 F1 while removing 92% of tool-output input tokens on its curated evaluation. Those figures miss the requested 95% reduction and are not end-to-end coding success or a Wrench result. |
| Local general coding worker | Treat Qwen3.5-4B or a code-specialized 3B-7B model as a later, separate local-worker comparison only if the product requires local code generation. Do not claim that a model-card score or a short repository task establishes all-day coding. | No candidate has a Wrench-specific sustained-engineering result or a current admitted full-day runtime. The 4B and coder models need candidate-specific inventory, adapter/runtime compatibility, measured context headroom, and paired repository sessions. |
| Sustained coding in the proposed hybrid | Keep the stronger coding model behind the user-specified SubRoute `http://127.0.0.1:4000`; use Wrench to reduce and structure mechanical context work. | The route is presently for read-only inspection. Its aggregate spend cap and complete caller-side hard-cap/usage receipts are not established, so this report made no generation request. A healthy route is not cost or model-identity evidence. |

This yields two distinct answers. **For a Wrench context gateway, test 0.8B first and use 2B as the next capacity challenger. For a local model expected to implement code, 4B or a code-specialized 3B-7B is a separate research problem.** If “work all day long” means the whole system, a capable coding worker can do the semantic engineering while Wrench handles context mechanics. If it means the small local Wrench model must itself complete nearly every open-ended engineering task without the stronger model, present evidence does not support that requirement.

## What the strongest nearby evidence says

### LoRA can specialize a small tool model, but not make it a general engineer by default

[Squeez](https://arxiv.org/abs/2604.04979) fine-tunes Qwen3.5-2B with LoRA for a narrow task: given a focused query and one tool output, copy only the smallest verbatim evidence spans that should be inspected next. The paper reports 0.86 recall, 0.80 F1, and 92% input-token reduction against its evaluation. This is a direct match for one useful Wrench role: pruning noisy tool output without rewriting facts.

The paper's [published dataset card](https://huggingface.co/datasets/KRLabsOrg/tool-output-extraction-swebench) makes the limits visible. The released v3 dataset lists 11,366 rows, including 10,508 train, 240 dev, and 618 test examples; the test set was manually curated and excluded 111 problematic examples. Its SWE portion is repository-split, but the held-out repositories are xarray and Flask; most non-Python test coverage is synthetic. The task measures extraction against spans, not whether a coding agent fixes issues, preserves solve rate after compression, or works for an eight-hour session. The paper's abstract says 11,477 examples while the current dataset card lists 11,366 after the described exclusions. This is promising task evidence, not a transferable Wrench efficacy claim.

### LoRA is a reasonable first adaptation method, with data transfer still a risk

The September 2026 controlled study [SFT or RL for Tool-Calling Agents?](https://arxiv.org/abs/2609.17848) compares SFT with LoRA and GRPO over Qwen3 sizes from 0.6B to 32B. Its authors report that LoRA SFT is strongest in-distribution in 15 of 18 settings; cross-dataset methods are closer, and dataset mixing helps transfer. This supports a small, reviewed SFT/LoRA candidate as a practical first experiment. It does not imply that a Wrench dataset transfers to real repositories or that a LoRA meets Wrench's quality and savings gates.

### Strict host validation matters more as model size shrinks

A 2026 [sub-2B tool-calling reliability study](https://arxiv.org/abs/2609.07370) reports a best recovered-call score of 79% for Qwen2.5-1.5B in its 100-prompt setup, while a strict raw-response audit found only five of 1,000 responses directly parseable as JSON. It is a small, non-MCP end-to-end benchmark and should not be treated as a general estimate, but it illustrates why “valid JSON after a recovery parser” is not enough. Wrench must validate typed output, reject unknown IDs and fields, and abstain safely. A deterministic parser is still not a semantic correctness oracle.

### Multi-role LoRA coding evidence uses larger models and bounded benchmarks

[MapCoder-Lite](https://arxiv.org/abs/2509.17489) specializes one 7B model with role-specific LoRAs for retrieval, planning, coding, and debugging. It reports better results on xCodeEval/APPS/CodeContests and lower memory/token generation time than its multi-agent baseline. This supports role specialization as a research pattern, but it does not show that a 0.8B or 2B gateway can handle all-day repository engineering. Its benchmark tasks are also not the Wrench workload.

The official [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) and [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) cards identify the small checkpoints as suitable for prototyping and task-specific fine-tuning and list Apache 2.0 licensing. Their reported general, agent, and coding benchmarks are model-author measurements, not Wrench effectiveness evidence. The 2B card is useful to narrow the candidate; it cannot justify a download, training job, or product claim by itself.

## Reconcile savings, completion, and engineering

The current Wrench research goal defines local completion as a task episode completed without a frontier call. It separately requires verified success retention, frontier-token savings, and all-in dollar savings. Keep those definitions. A gateway that reduces the coding model's prompt but still calls it on almost every task may save tokens, but it does **not** meet a 95% no-frontier episode target.

Also report mechanical coverage separately from full task completion. “Wrench handles 95% of mechanical input work” is not the same claim as “95% of engineering episodes complete successfully without the coding worker.” Do not substitute one denominator for the other.

The 95% all-in cost reduction is stricter than a 5% call rate. If `C` is the direct coding-worker cost, the hybrid must satisfy `frontier cost + local inference + energy + hardware/runtime allocation + training/evaluation amortization + human rescue <= 0.05*C`. Difficult escalations can dominate spend. Count full serialized requests, tool schemas, cache-hit/miss billing, tool output, context rebuilds, retries, verification, recovery fetches, and local compute. Use the actual SubRoute response/provider receipts when a separately authorized capped study becomes possible.

The external Squeez result also shows the quality/savings tension directly: 92% removed is less than 95%, while 0.86 evidence recall is not evidence of 95% preserved task quality. Exact-source fallback can recover omissions, but recovery adds tokens and latency. Wrench must measure the total after recovery, not the first compressed message only.

## Wrench evidence that changes the next step

- The existing synthetic tokenizer screen measured 3,204 baseline versus 2,816 prepared input tokens over five eligible pairs: 12.1099% ratio-of-sums reduction. Two positive cases were excluded for failing source-evidence gates; four abstention cases passed. It made no provider calls, so frontier-token savings remain unmeasured. It is exposed one-shot data and must not be rerun or used for training.
- The tested Qwen3.5-0.8B general semantic controller scored 0/10 on its tool-backed screen. That closes its general-controller claim but does not directly test a new Wrench LoRA on narrow extraction decisions.
- No Wrench LoRA adapter or held-out quality result exists. One-step training preflights establish only selected-module/runtime compatibility.
- The OpenCode context hook protects the tool schema and runs before final request lowering. Therefore current E0 cannot claim tool-schema filtering or full-request savings. The no-provider request-accounting seam must capture the whole bounded lowered body and retry/stream lifecycle before making a cost claim.
- Current host RAM has repeatedly fallen below the candidate's 25% fit-start buffer. The last fit preflight is not authorization to start a full fit. Recheck storage, RAM, VRAM, exact identities, and candidate-specific admission at job start.

The 12.11% screen is currently the only measured Wrench token-reduction result. It does not support a 95% claim. The Squeez figures are external evidence for choosing a useful next task and scale, not an estimate of Wrench performance.

## Recommended experiment sequence

1. **Finish full-request accounting with no provider call.** At the actual request boundary, measure serialized `messages`, tool schemas, history, tool/file output, auxiliary requests, retries, cache-relevant input, and exact byte/token identities. Preserve the existing protected OpenCode hook fields. Use synthetic fixtures only until an approved real-task data plan exists.
2. **Establish deterministic mechanics first.** Compare capability-aware allowlisted tool-schema filtering, output extraction, and exact source-span retrieval against a no-filter baseline. Preserve every required/authorized tool; keep originals locally and test omissions and recovery. Report gross tokens removed and net tokens after refetch/retries separately.
3. **Train and compare the smallest admitted LoRA.** Keep the staged 0.8B run as the first feasibility candidate when its 25% RAM-start and 10% RAM/VRAM runtime gates pass. Compare deterministic policy, frozen 0.8B, and Wrench LoRA on the same fresh, repository/task-group-held-out, synthetic-only mechanics set. A valid schema is a component metric, not the outcome.
4. **Only then justify 2B.** Advance Qwen3.5-2B if the 0.8B held-out failure is specifically capacity-related and the 2B inventory, storage peak, runtime/LoRA targets, and device admission pass. Do not download or train from the Squeez paper's model size or VRAM estimate alone. Keep public research datasets and benchmark holdouts out of Wrench training unless separately cleared and admitted.
5. **Test all-day engineering as a distinct system study.** Pair a frozen coding worker alone with Wrench plus the same worker on clean task snapshots. Record accepted fixes, tests, human rescue, unauthorized edits, full costs, pauses, context switches, restarts, and recovery. Keep the predeclared ten independent eight-hour sessions across repositories/languages; short screens cannot satisfy it.
6. **Use SubRoute only after cap enforcement is real.** The user's route is `http://127.0.0.1:4000`. Before any generation, the owner must provide a numeric aggregate cap and the caller must enforce it fail-closed while preserving actual model/provider, usage, and billing receipts. Route health or `/models` does not prove provider choice or cost.

## Sources

- [Squeez paper, arXiv:2604.04979](https://arxiv.org/abs/2604.04979)
- [Squeez dataset card and split construction](https://huggingface.co/datasets/KRLabsOrg/tool-output-extraction-swebench)
- [SFT or RL for Tool-Calling Agents?, arXiv:2609.17848](https://arxiv.org/abs/2609.17848)
- [Beyond Fluent Generation, arXiv:2609.07370](https://arxiv.org/abs/2609.07370)
- [MapCoder-Lite, arXiv:2509.17489](https://arxiv.org/abs/2509.17489)
- [Official Qwen3.5-0.8B card](https://huggingface.co/Qwen/Qwen3.5-0.8B)
- [Official Qwen3.5-2B card](https://huggingface.co/Qwen/Qwen3.5-2B)
- [Current Wrench proof design](../../evals/wrench-gateway-model-research/product-proof-design-20260927.md)
- [Latest Wrench request-accounting gap](../../evals/wrench-gateway-model-research/iteration-025-request-accounting-gap-20260927.md)
