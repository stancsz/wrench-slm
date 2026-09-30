# Teacher–student distillation protocol for Wrench

Date: 2026-09-30 (America/Edmonton)  
Scope: provider-free decision and experiment protocol; no model download, inference, training, SubRoute request, or held-out access.  
Decision status: research recommendation, not a selected model or product result.

## Recommendation

Use **Spark-X2.5-4B as a candidate local teacher** and **Qwen3.5-2B as the first student to evaluate**, with a 4B Wrench LoRA as the size challenger only if the 2B arm fails a named, verified capacity gate. This is a role-based order. Do not train the student to imitate Spark's general code-writing behavior. Train it to propose bounded, typed context actions that deterministic Wrench code can validate and execute.

This is plausible because the Spark-X2.5 repository publishes 4B and 1.7B model variants and describes multi-teacher on-policy distillation as part of its own post-training. Its 4B model card reports stronger coding/tool-use benchmark values than its 1.7B card. The public recipe does not expose the teacher traces or enough detail to reproduce Spark's internal distillation. Downloading a student/teacher checkpoint therefore provides model weights, not access to the training corpus, teacher ensemble, reward signal, or exact method used to create those weights. Spark can supply new Wrench-specific labels only by producing reviewed traces for Wrench's own tasks.

Qwen3.5-2B is the first student candidate because the current Wrench evidence review identifies it as a credible extractive controller size, its official Base card describes LoRA/PEFT fine-tuning, and its pinned inventory is materially smaller than the 4B checkpoint. None of this proves local runtime compatibility, a successful Wrench LoRA, or task utility. The 4B student/teacher remains a challenger, not a presumption that scaling up wins.

## What to distill

Each training record should bind a canonical episode manifest and contain:

- The redacted task and exact source/tool observation identities, with hashes and rights/review provenance.
- The teacher's bounded proposal as a typed action: selected evidence/span IDs; a retrieval or recovery request; a context budget/depth; or `keep`, `abstain`, or `escalate`.
- The deterministic validator's decision, resulting prepared context, and hash of its actual text.
- An outcome label from executable task verification, including failure, regression, timeout, human rescue, and abstention. Teacher confidence or agreement alone is not an outcome label.

Do **not** distill arbitrary shell, unrestricted tool arguments, credentials, permission choices, autonomous code changes, unverified factual paraphrases, or provider-routing authority. Parsers, exact-span recovery, budgeting enforcement, provenance, verification and rollback stay deterministic. Prefer selecting exact evidence spans over rewriting them; if a summary is proposed, retain source links and score recovered facts independently.

Because teacher and student tokenizers may differ, train against the structured action and source-span identifiers, not teacher token IDs or logits. The deterministic renderer produces the real UTF-8 prompt text. Count tokens with the tokenizer/model actually used at each endpoint; never send local token IDs as if they were a provider's tokens. For any future frontier arm, provider-reported usage is a separate receipt and mock data is never billed or counted as a frontier call.

## Data and fitting sequence

1. Freeze the episode manifest, task fixtures, split assignment, tokenizer/model identities and deterministic-only baseline. Keep the final held-out split sealed. The current goal-file hash mismatch must be resolved through the established goal/package review process before a model job.
2. Obtain eligible Wrench-specific teacher traces from a pinned, licensed model under exact package, rights and host-resource admission. Have deterministic validators and human review resolve disagreement; quarantine ambiguous or unverified traces.
3. Train a new inactive Qwen3.5-2B LoRA from approved train records only. Keep Wrench-Core and foundation frozen. Record exact model/tokenizer/adapter hashes, data lineage, step schedule, optimizer/peak-storage estimate, device and resource trace.
4. Select checkpoints only on a development split using predeclared bounded-action measures and verified task outcomes. Compare against deterministic-only and no-LoRA controls. Do not tune on or reveal sealed held-out labels.
5. Run paired full-episode evaluation on the frozen held-out battery only after identity review and resource admission. Preserve every failure and all denominators; report confidence intervals and paired discordances.
6. If 2B misses a specified gate, inspect failure categories first. Test the 4B arm on the same tasks only if the additional RAM/VRAM, latency, and storage budget is admitted. Activate nothing unless evaluated, atomically switchable, and rollback-tested.

## Evidence needed to call distillation useful

The teacher/student experiment is a component study, not the product acceptance study. Record at least:

- Exact-evidence precision/recall, omitted-required-evidence rate, unsupported-span rate, abstention and escalation calibration.
- Verified episode completion, regressions, retries, recovery fetches, cache misses, human rescue, tool/test results and paired success discordances.
- Full lifecycle frontier input/output tokens and route count, but only in an explicitly authorized and metered frontier experiment. Separately count local prompt/response tokens and deterministic processing; compression alone is not frontier-token savings.
- All-in cost, including local compute/energy, runtime allocation, training amortization, operator time, verification and repair. Also report p50/p95 latency and sustained resource headroom.
- Multi-repository/language coverage, long sessions, interruption/restart, state recovery, repeated runs and regression tests. Short synthetic screens are not evidence of all-day engineering.

Keep the campaign gates unchanged: at least 95% verified local completion, no more than 5% frontier-routed episodes, at least 95% of frontier-only verified success retained, at least 95% fewer full-lifecycle frontier tokens and at least 95% lower all-in cost on the same frozen representative tasks. The current work has not established any of these product claims. If teacher/student improves extraction but not end-to-end outcomes, keep the result as a component finding and do not call the project successful.

## Risks and stop conditions

- **Teacher imitation ceiling:** a small student cannot be expected to inherit all coding ability from an output-only teacher. The target is bounded context decisions, not full coding-agent distillation.
- **Teacher label noise:** Spark outputs are hypotheses. Require source-linked actions and outcome-based acceptance; disagreement is reviewed rather than majority-voted into truth.
- **Tokenizer mismatch:** compare rendered text and endpoint token counts, not token IDs across models.
- **Compression harms utility:** preserve exact hot evidence and measure task outcomes. Low token count receives no credit when verification fails or recovery cost erases the saving.
- **Resource and identity gates:** no weight download or inference until the exact model inventory, license, runtime, destination headroom, storage reservation and RAM/VRAM gates are current. Fit-03's review is not authorization for another model or training job.
- **Provider accounting:** no generation through SubRoute until its current route and caller identity are verified and the required campaign-wide cap and durable metering authority exist. This protocol does not grant that authority.

## Sources

- [Spark-X2.5 official repository](https://github.com/XHToken/Spark-X2.5): public model variants, integrations and high-level post-training description.
- [Spark-X2.5-4B official model card](https://huggingface.co/XHToken/Spark-X2.5-4B): published model-card training and benchmark claims; vendor-reported, not Wrench results.
- [Spark-X2.5-4B-Base official model card](https://huggingface.co/XHToken/Spark-X2.5-4B-Base): license and fine-tuning guidance to verify against the exact revision before any use.
- [Qwen3.5-2B official model card at reviewed revision](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/README.md) and [Qwen3.5-2B-Base](https://huggingface.co/Qwen/Qwen3.5-2B-Base): candidate identity and published fine-tuning guidance; local compatibility remains untested.
- [Multi-Teacher On-Policy Distillation paper](https://arxiv.org/abs/2606.30406): background method. It is not proof that Spark's undisclosed implementation matches every paper detail.
- Wrench's [Iteration 229 model-size refresh](../../reports/wrench-gateway-model-research/model-size-research-refresh-iter229-20260930.md) and [context-compression evidence refresh](../../reports/wrench-gateway-model-research/compression-evidence-refresh-20260930.md): provisional Wrench decision and evidence limits.

## Execution record

Storage was `WITHIN_LIMIT` before writing: actual `32,711,113,579` bytes, active reservations `36,103,000` bytes, including the Docker Ollama model volume and hourly automation directory. A unique 30,000-byte documentation reservation was admitted; the destination was C: with more than 100 GB free. Fresh pre-write sample: 25.92% system RAM free and 15,214/16,311 MiB VRAM free. No local model process was identified. No model, provider, SubRoute, credential, or held-out operation occurred.
