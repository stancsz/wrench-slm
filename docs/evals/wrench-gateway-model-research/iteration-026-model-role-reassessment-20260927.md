# Iteration 026: small-model role reassessment

Date: 2026-09-27 (America/Edmonton)  
Status: research and scope decision complete; no model/provider run  
Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)  
Report: [Wrench gateway model decision reassessment](../../reports/wrench-gateway-model-research/decision-reassessment-20260927.md)

## Finding

The most realistic role for a small Wrench LoRA is task-conditioned, extractive selection of evidence from tool output. Deterministic code should own exact parsing, tool authorization/schema filtering, retrieval, source identity, token accounting, context assembly, and validation. A separate stronger coding worker should handle diagnosis, design, semantic code edits, and recovery from ambiguous failures.

New external evidence strengthens Qwen3.5-2B as a future context-pruning challenger: the Squeez preprint reports a Qwen3.5-2B LoRA removing 92% of tool-output input tokens with 0.86 recall and 0.80 F1. The released dataset card lists a 618-example manually curated held-out split. This is extraction quality on one observation, not downstream solve-rate retention, full gateway savings, or all-day engineering. It does not clear Wrench's 95% gates.

For the current staged Wrench path, retain 0.8B as the first feasibility candidate because its snapshot and training protocol are already staged. Do not start a fit below the existing 25% free-RAM start gate. Consider 2B only after a measured held-out capacity failure, with its own pinned inventory and resource/storage admission. A 4B or code-specialized 3B-7B local coding worker remains a separate, unproven comparison.

## Reconciled product claim

The current goal's “local completion” means a task episode completed without any frontier call. It is not equivalent to Wrench handling 95% of mechanical/context operations while a coding model is still called for most tasks. Keep full task completion, mechanical coverage, frontier-token savings, and all-in dollar savings as separate denominators. The system may support sustained engineering through a capable coding worker, but no local gateway model has evidence for independent all-day coding.

## Wrench evidence snapshot

- The prior one-shot tokenizer screen measured 12.1099% ratio-of-sums input reduction over five eligible synthetic pairs; two positive cases failed evidence gates, and no provider calls occurred. Frontier-token savings remain unmeasured.
- Qwen3.5-0.8B's general semantic screen remains 0/10. It did not test a Wrench-specific LoRA on bounded extraction decisions.
- No Wrench LoRA adapter or held-out quality result exists. A one-step preflight is compatibility evidence only.
- The context hook protects `tools` and runs before final request lowering. The next no-provider integration should account for the complete lowered request, tool schemas, history, file/tool output, retries, cache-relevant input, and exact source recovery.
- SubRoute `http://127.0.0.1:4000` remains a read-only comparison/teacher route. No generation request was made because the numeric aggregate spend cap and hard caller-side cost/usage receipt controls are not in place.

## Sources reviewed

- [Squeez paper](https://arxiv.org/abs/2604.04979) and [released dataset card](https://huggingface.co/datasets/KRLabsOrg/tool-output-extraction-swebench)
- [SFT or RL for Tool-Calling Agents?](https://arxiv.org/abs/2609.17848)
- [Beyond Fluent Generation](https://arxiv.org/abs/2609.07370)
- [MapCoder-Lite](https://arxiv.org/abs/2509.17489)
- Official [Qwen3.5-0.8B](https://huggingface.co/Qwen/Qwen3.5-0.8B) and [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) model cards

## Scope and storage

- Wrench HEAD at start: `af01304824f079a64b6c3902397a2034b843511a`.
- Only the reassessment report, this iteration note, and the gateway goal links/findings were edited. Existing user worktree changes were preserved.
- No model selection/download, training, model inference, benchmark, SubRoute generation, or test run occurred.
- Documentation job reservation: `WRENCH-RESEARCH-REASSESSMENT-20260927-01`, 200,000 bytes. Initial storage status was `WITHIN_LIMIT`; the reservation was released only after the final documentation files were accounted for.
