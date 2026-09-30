# Iteration 140: exact symbol-span evidence selection

Date: 2026-09-28 (America/Edmonton)  
Assignment: WRENCH-EXACT-SYMBOL-SPAN-PAIR-REPEAT-ITER140  
Status: **three synthetic lookup tasks passed the Wrench-prepared arm; local-tokenizer compression crossed 95%, target-tokenizer compression did not**  
Repository HEAD: af01304824f079a64b6c3902397a2034b843511a (working tree dirty)  
Gateway-goal SHA-256: B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027

## Change

The E0 context pipeline now has an opt-in `use_symbol_span_for_required_path` mode. For an explicit `symbol:<exact name>` query, a parser-verified symbol span can satisfy a required source path, while its full-file content hash, snapshot hash, artifact handle, parser identity and exact line range remain in the source reference. Whole-file preservation remains the default, and preserve-source paths still require the whole file. The local MVP runner opts in to the span mode.

The focused E0/source tests passed: **30 passed**. During that check, an over-limit required-ID validation case exposed status-precedence behavior; it was corrected so invalid input is reported as `invalid_input`, not overwritten as `context_failed`. The paired model run was repeated after that correction, against the final source hash.

## Paired local-model result

The final run used the same three authored, answer-blind synthetic lookups and fixture in both arms. Both arms used Qwen/Qwen3.5-0.8B BF16 at revision `2fc06364715b967f1860aea9cf38778875588b17`; no adapter was loaded. The exact fixture SHA-256 is `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.

| Measure | Full fixture | Wrench E0 | Result |
|---|---:|---:|---:|
| Qwen input tokens | 26,196 | 1,249 | 95.232097% fewer |
| Qwen input + output tokens | 26,226 | 1,275 | 95.138412% fewer |
| Answer-blind verifier passes | 2/3 | 3/3 | One more verified case in this tiny sample |
| Required source quotes visible | not applicable | 7/7 | All selected required quotes retained |
| MiniMax M3 target-tokenizer prompt tokens | 19,297 | 1,520 | 92.123% fewer |
| Frontier calls / frontier-token savings | 0 / N/A | 0 / N/A | No frontier comparison occurred |

This is evidence that exact symbol-span selection can preserve the fixture's required evidence while reducing the local model's prompt size on these three examples. The 95% local-tokenizer result is a **component measurement**, not the product target. The provider-target tokenizer measured about 92.1% reduction, and actual full-lifecycle frontier-token savings remain unavailable.

The first run, `WRENCH-EXACT-SYMBOL-SPAN-PAIR-ITER140`, is retained as a preliminary observation. Its paired local reductions were 95.220644% input and 95.126973% input-plus-output; its target-tokenizer result was 92.08%. It ran before the validation status-precedence fix. Do not pool its result with the repeated final-source run.

## Exact receipts and identities

| Item | Identity |
|---|---|
| Final paired receipt | `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter140-symbol-span-repeat.json`, 6,110 bytes, SHA-256 `7D9A6F14322A5A410844DFEDC42EDB36E1036903CD4DDB55086124E1821437C6` |
| Preliminary paired receipt | `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter140-symbol-span.json`, 6,105 bytes, SHA-256 `509A72356462A5ECC8CBEB7BDD1B345422F1366A9E7313BA1404CBB6D356935F` |
| Final E0 pipeline | SHA-256 `20830417FCE0C09B5855A8FD08B02AC8834981C8ACCDFFFABF629FDA4C2A16C7` |
| Focused test file | SHA-256 `809EB9AA39760EA326FD26D570A1BED5FB5F2F044B4D9FA58AE6CA49AFAC3EC5` |
| Goal file | SHA-256 `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` |

The final run completed in 42.57 seconds with 55 resource samples. Its lowest sampled free RAM was 13.476% and lowest free VRAM was 75.182%, above the 10% run floor. Peak CUDA allocated/reserved memory was 2,678,108,160 / 2,894,069,760 bytes. It used a local NVIDIA GeForce RTX 5060 Ti, CUDA 13.2, PyTorch 2.14.0+cu132, and Transformers 5.17.0. No provider spend occurred.

## Limits and next gap

The workload contains only three authored lookups against a repetitive fixture. It is not a representative coding battery or sustained engineering test. Both arms use the same local base model. There is no trained Wrench LoRA, no frontier-only baseline, no routing-rate estimate, no success-retention confidence bound, no all-in cost accounting and no measured frontier-token savings. A single additional pass in three cases is not a stable quality estimate.

Next, extend the frozen task set with realistic code-navigation and mechanical-edit cases, including config/key lookups, stale/missing evidence and recovery fetches. Preserve lossless hot evidence and measure the target provider tokenizer plus the full lifecycle. Do not enable alternative raw-source serialization without injection/collision and behavior checks. Then resume the independently reviewed LoRA candidate workflow only after its package, RAM, storage and destination gates admit it. The full gateway goal remains active and unproven.
