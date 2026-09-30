# Iteration 141: target-tokenizer prompt-envelope ablation

Date: 2026-09-28 (America/Edmonton)  
Assignment: WRENCH-PROMPT-COMPONENT-ABLAT-ITER141  
Status: **best tokenizer-only variant reached 94.190807% target-tokenizer input reduction; product frontier savings remain unmeasured**  
Repository HEAD: af01304824f079a64b6c3902397a2034b843511a (working tree dirty)  
Gateway-goal SHA-256: B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027

## Question

Iteration 140's answer-blind three-case run measured 92.123% fewer MiniMax M3 target-tokenizer prompt tokens after exact symbol-span selection. The next target was to identify which transmitted context-envelope components account for the remaining gap to 95%, without running model generation or changing runtime behavior.

## Method and result

The offline script prepared the same three synthetic prompts, then counted full chat-template tokens after controlled string-level variants. It loaded the pinned local tokenizer assets, but no model weights. The repeated full-fixture target baseline was 19,297 tokens; the current Wrench materialization was 1,530 tokens in this fresh count.

| Prompt form | Target input tokens | Reduction from 19,297 | Local Qwen input tokens | Local reduction |
|---|---:|---:|---:|---:|
| Current Wrench JSON wrapper | 1,530 | 92.071306% | 1,254 | 95.213010% |
| Current trust wrapper, unescaped text block | 1,488 | 92.288957% | 1,237 | 95.277905% |
| Compact `[E1]` style labels, current JSON wrapper | 1,250 | 93.522309% | 833 | 96.820125% |
| Short trust warning, text block and compact labels | **1,121** | **94.190807%** | **729** | **97.217132%** |
| Raw selected text without trust boundary, diagnostic only | 1,296 | 93.283930% | 1,039 | 96.033746% |

The best measured candidate remains 156 target-tokenizer tokens above the 5% ceiling of 964.85 tokens. The current wrapper contributes some measurable overhead, and long context IDs are expensive for both tokenizers. Raw selected text is not a viable candidate because it removes the untrusted-source boundary. The short-warning/text-block variant retains a warning and delimiters, but its string-level ID rewrite has not been implemented against typed source spans and has not been validated against injection, collisions, or downstream answers. **No production format was changed.**

The result gives the next concrete engineering lead: build compact labels from the selected source-reference records rather than rewriting a rendered string, retain exact file/span provenance in the external receipt, then rerun adversarial and answer-blind checks. If path labels are required for a task, include short exact paths and line spans and count their cost. Do not omit source identity when it is needed for the task.

## Identity and receipt

The tokenizer decomposition utility SHA-256 is `BDBEF8D965A5DA0003E8C0486AD7E6ED73872CCE501F59DAAAFC2332EAD4CCD3`.

The tokenizer-only receipt is `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\iter141-prompt-component-decomposition.json` (6,400 bytes, SHA-256 `9A4642AF0DEF59EA50002F1F30BAA1E99002BCF2E9A5D4B5FDA714A3D47D4DD6`). It records per-case target/local counts, source hashes, quote-coverage checks, tokenizer identity, and diagnostic limits. The source utility is [decompose_gateway_prompt_tokens.py](../../../tools/decompose_gateway_prompt_tokens.py).

The paired workload was the same authored fixture and answer-blind task IDs used in Iteration 140. Required quotes were present in all three prepared cases. Expected answers did not appear in their questions. The receipt includes exact source file hashes for the fixture, prompt runners, ledger, E0 pipeline and prompt compiler.

## Limits

This was a tokenizer-only ablation on three synthetic lookup tasks containing repetitive health logs. No model output, quality verifier outcome, real coding work, adapter, provider request, frontier token, recovery fetch or cost was measured. The 94.19% number is not a Wrench product result. The variants do not establish prompt-injection safety or path/citation correctness. Local Qwen reduction cannot substitute for target-tokenizer or frontier usage accounting. The overall gateway goal remains active and unproven.
