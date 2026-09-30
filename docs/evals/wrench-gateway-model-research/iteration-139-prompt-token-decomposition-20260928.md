# Iteration 139: prompt token decomposition and evidence-scope ablations

Date: 2026-09-28 (America/Edmonton)  
Assignment: WRENCH-E0-PROMPT-TOKEN-DECOMPOSITION-ITER139  
Status: **tokenizer-only format ablation exceeded 95% local input reduction on three synthetic prompts; target-tokenizer and task-quality gates remain below/unmeasured**  
Repository HEAD: af01304824f079a64b6c3902397a2034b843511a (working tree dirty)  
Gateway-goal SHA-256: B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027

## Why

The answer-blind paired baseline's prepared prompt remained slightly above 5% of full-context local-model input. This iteration measured which part of the emitted E0 message accounts for the remaining input and tested whether broad required-path inclusion could be removed without losing the fixture's required source lines.

The tokenizer-only run reconstructed the same three authored lookup prompts at E0 context budget 64. It used the local Qwen tokenizer and the pinned MiniMax M3 tokenizer/template, but did not load model weights or generate answers.

## Prompt-format ablation

The full-context baselines totaled 26,196 Qwen input tokens and 19,297 MiniMax-template input tokens. The current E0 rendering and three candidate renderings produced:

| Rendering | Local prepared input | Local reduction | MiniMax prepared input | MiniMax reduction |
|---|---:|---:|---:|---:|
| Current JSON-string wrapper | 1,344 | 94.869446% | 1,631 | 91.547909% |
| Shorter warning, JSON string retained | 1,320 | 94.961063% | 1,607 | 91.672281% |
| Current warning, source text block | 1,313 | 94.987784% | 1,571 | 91.858838% |
| Short warning and source text block | **1,229** | **95.308444%** | 1,487 | 92.294139% |

The text-block profile saves 115 Qwen input tokens and 144 MiniMax-template input tokens against the current rendering in this within-run comparison. It crosses 95% only for the local tokenizer. The result is a prompt-format count, not model utility, frontier usage, a 95% product result, or evidence that the text-block format is safe. The variant did not test marker collisions, prompt injection, source instructions, or downstream behavior. **Do not enable it in production based on this count.**

For reproducibility, the exact tokenizer-only output is stored at C:\wrench-slm-data\artifacts\wrench-gateway-model-research\tokenizer-ablation-iter139-20260928.json (3,733 bytes, SHA-256 E9CAF1278FCD2CC27A70BAA917E6C5B80D463915B6CFF9F154F77A0D66FFE4D7). It binds the fixture, repository revision, model/tokenizer revisions, all measured variants, the setup failures, and the limits above.

Iteration 129 previously measured 1,356 Qwen and 1,627 MiniMax prepared input tokens. This fresh materialization measured 1,344 and 1,631 respectively, with the same 26,196 / 19,297 full-context totals. Snapshot-bound evidence identifiers include randomized temporary-root identity and can change tokenization slightly across preparations. Treat the variant deltas in this report as paired within-run counts; do not present the small cross-iteration differences as a confirmed regression or improvement.

## Required-source-path ablation

I repeated the three preparations after temporarily omitting required_source_paths, leaving the existing post-preparation exact-quote check enabled. Retry policy retained 3/3 required quotes and retry-function retained 2/2, but session-lifetime failed with required_source_quotes_missing. Therefore complete-coverage savings are undefined. The per-case token numbers are retained in the JSON receipt but cannot be averaged as a passing all-case result.

This establishes a concrete retrieval gap: making the required source path mandatory preserves coverage but can bring broad file content into the prompt; removing that whole-path guarantee loses required evidence on one of these three queries. The next engineering step is line/span-level source selection with exact snapshot provenance and explicit omission/abstention, followed by the same answer-blind paired task verifier. Whole-path inclusion remains the known-good control.

## Exact identities

| Input | SHA-256 or revision |
|---|---|
| Qwen model | Qwen/Qwen3.5-0.8B@2fc06364715b967f1860aea9cf38778875588b17 |
| Synthetic fixture | 92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1 |
| MiniMax target tokenizer | MiniMaxAI/MiniMax-M3@f0e1c1e04d40177e4673a22097036854f536e9c0 |
| Paired runner | C2A89358838D7FADBACAD1D0DD9535C584430AB723CD72D17EB761320DB689DF |
| Local context runner | 5F564296CC6D653C68C18EB921DCC19AF025902CB7DE4F6E35D3E80CDB5E9CFF |
| Prompt compiler | 2930238C48D4162A88944D9A6CC82FC5398C11A1503EAE9B12AC5AE2F9381DDF |
| E0 pipeline | 4EA3E320EABA9DFA0FCBC3686E4EDEDC432AC7B06631A9132A06219F9C463C04 |

The tokenizer-only runtime was Transformers 5.17.0, tokenizers 0.23.2, and huggingface-hub 1.33.0. No adapter, model generation, frontier call, spend, or held-out data was used.

## Preserved failures

The first format-decomposition invocation failed before producing counts because its prefix assertion expected an extra newline. It changed no source and wrote no receipt. The corrected run produced the complete table above.

The required-path ablation is a substantive fail-closed result, not a successful token-savings run: session-lifetime lost required evidence. No all-case ratio is reported for that branch.

## Admission and limits

Reserved 25,000,000 bytes under this assignment before tokenizer preparation. Storage status before the report was WITHIN_LIMIT, including the approved data root, SubRoute, active worker checkout, hourly automation folder, and Docker WSL model volume. The scan measured 15,436,398,602 actual bytes plus 31,103,000 bytes of active reservations, or 15,467,501,602 projected bytes against the 50 GB ceiling. No model inference ran; the measured host sample before tokenizer-only analysis was about 19.26% RAM free and 15,223 / 16,311 MiB VRAM free.

The result does not establish a safe replacement serialization, LoRA behavior, 95/5 completion/routing, 95% frontier-token reduction, lower all-in cost, or all-day engineering. The complete product goal remains active and unproven.
