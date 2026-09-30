# Iteration 205 static review

Date: 2026-09-29 (America/Edmonton)  
Review job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER205-REVIEW-20260929-01`  
Review nonce: `ac933883-cd26-4495-9f39-a303f91d110f`

## Verdict

**Conditional fail for interpretation; do not treat an Iteration 205 receipt as protocol-conformant until the findings below are fixed.** This was a static source review only. No test, model load, inference, benchmark, network request, or held-out access occurred.

Identity checks passed: HEAD `af01304824f079a64b6c3902397a2034b843511a`; active goal SHA-256 `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`; runner SHA-256 `bba9d87c38468ce1793f1af255291e9662ac9c396cfb776ffa7699776d079bbf`; protocol SHA-256 `94ee1bdd7780eef481b9e42f0fe86e1ea57f4ba7c0accbaedf094eae8e5b4ee6`. Runner and protocol agree on experiment job ID and nonce, pinned model revision, inventory and snapshot receipt hashes, adapter weights/config hashes, output path, and required goal/HEAD.

## Material findings

1. **Verifier is not exact-string despite the protocol.** `answer.strip("` \n\t") == expected` accepts answers with surrounding whitespace or backticks. Compare the decoded answer directly to `expected`, or revise the protocol and claim consistently.
2. **Token-reduction summaries can use incomplete pairs.** `denominators_valid` checks only for a positive full-context denominator. A partial/aborted run with full-context rows but missing Wrench-context rows still reports a reduction ratio. Emit ratios only when all six cases have exactly one row in each context arm for that model arm, with matching case IDs; otherwise use `null` and mark the summary incomplete.
3. **Protocol runtime identity is not fully enforced or recorded.** Package and CUDA versions are gated, and device name is recorded, but Python 3.13 and RTX 5060 Ti are not gated; Python version is not recorded. Add checks/receipt fields or weaken the protocol requirement explicitly before the run.
4. **Failure receipts are not sealed for early aborts.** Errors during model/runtime imports, identity checks, resource admission, or model/adapter load raise before a receipt is written. The loop does preserve partial rows, but early failures leave no durable failure receipt, contrary to the protocol's requirement to record failed or aborted cases. Write a bounded failure receipt for these stages too, without masking the original error.
5. **Runner does not enforce storage admission.** The protocol requires a fresh checker status/reservation and 5 GB physical C: headroom. The runner checks the output path and refuses a preexisting receipt, but does not verify active reservation, aggregate budget, free disk, or output creation atomically. These remain external operator gates; document that they were satisfied in the run evidence, and use exclusive/atomic receipt creation to avoid a check-then-write race.

## Pairing and safety observations

The four arms use the same case user prompt and system prompt; the full context includes all synthetic fixture files while Wrench context is generated from the same fixture snapshot using case-scoped source paths and table spans. Base/LoRA toggling is structurally correct: the same loaded PEFT model uses `disable_adapter()` for base and leaves the adapter active for LoRA, in eval/inference mode. Greedy decoding, token cap, and prompt hashes are recorded; context order alternates by case. However, model-arm order is always base then LoRA, leaving a systematic first-run/warm-up effect.

The helper checks evidence quotes before inference, but returns `required_quotes_visible` as an integer count; the runner copies it into a field whose name implies a boolean. Rename it to a count or return an actual boolean plus count.

A lightweight review-time sample was 30.11% free RAM and 15,200/16,311 MiB VRAM free. This is not run-time resource evidence. Runtime sampling every 0.5 seconds and a generation stopping criterion are present, but a brief breach between samples remains possible; resource minima and sample count are recorded when a receipt is produced.

The experiment nonce is `bd261641-cb41-48c1-bd3f-fdb6cc44e46f` in runner and protocol; it is separate from this review worker's nonce above.
