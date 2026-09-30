# Iterations 147-148: typed compact context and pruning ablation

Date: 2026-09-28 (America/Edmonton)  
Status: **typed compact formatting reached 94.149% target-tokenizer input reduction; an answer-blind required-quote pruning diagnostic reached 95.186%; no model or frontier outcome was measured**  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question

Can Wrench reduce prompt overhead further by assigning short labels to
structured selected segments, while keeping their exact identities in the
external provenance receipt and preventing source text from forging segment
headers or envelope markers?

## Implementation

The optional `compact_json_segments` prompt mode builds labels from the
selected segment records in selection order. Each label maps back to the
exact segment ID in `selected_evidence_ids` and the separate source-reference
receipt. The compiler checks each supplied text against the segment's
recorded SHA-256 before serialization. The prompt carries the selected text as
JSON string values, so quotes, fake `[context:...]` headers and marker-like
source text remain inside JSON strings. The existing JSON-string format
remains the default.

This mode is opt-in. It duplicates selected text in the bounded assembly
snapshot, which remains subject to the existing assembly byte limit. The
prompt does not include the provenance map itself; the request receipt must
retain it and bind it to the exact selected-ID ordering.

## Matched tokenizer counts

Both iterations used the same three authored synthetic lookup questions,
MiniMax M3 target tokenizer, Qwen 0.8B local tokenizer, full-fixture input, and
64-token Wrench selection budget. No model weights were loaded.

| Iteration 148 variant | Target input tokens | Target reduction | Local Qwen input tokens | Local reduction |
|---|---:|---:|---:|---:|
| Existing JSON-string context | 1,512 | 92.164585% | 1,256 | 95.205375% |
| Typed JSON segment pairs, shorter trust warning | 1,129 | 94.149350% | 708 | 97.297297% |
| Typed JSON text array, short warning | 1,054 | 94.538011% | 634 | 97.579783% |
| Typed JSON text array, minimal warning | 1,042 | 94.600197% | 622 | 97.625592% |
| Text array with no additional warning | 1,030 | 94.662383% | 607 | 97.682852% |
| Keep only segments containing predeclared required quotes, minimal warning | **929** | **95.185780%** | 502 | 98.083677% |

The tokenizer-only baseline was 19,297 target tokens and 26,196 local tokens.
The target tokenizer was the pinned MiniMax M3 tokenizer runtime (Transformers
5.17.0, Tokenizers 0.23.2, Hugging Face Hub 1.33.0); the local tokenizer was
Qwen/Qwen3.5-0.8B revision `2fc06364715b967f1860aea9cf38778875588b17`.
The target 95% ceiling is 964.85 tokens, so the normal typed formats remain
above it. The quote-segment diagnostic clears the ceiling by 35.85 tokens.
It retains every predeclared required quote on all three cases, but chooses
segments using those quote annotations. This is a diagnostic ceiling, not an
approved general pruning policy or a production result. Warning-free output
is diagnostic only; it is not an approved prompt format.

Iteration 147's structural-label variant counted 1,162 target tokens
(93.978339% reduction). The shortened-warning and text-array variants in
Iteration 148 improve that by another 33 to 132 tokens, depending on the
warning. Iterations 147 and 148 both leave meaningful room for evidence
pruning and envelope reduction.

## Checks and identities

- `tests/test_prompt_compiler.py`: 24 passed.
- `tests/test_prompt_compiler.py tests/test_e0_context_pipeline.py`: 48 passed.
- The adversarial compiler cases cover forged headers, marker-like source
  text and a tampered text/hash pair. The E0 integration case confirms compact
  mode retains the selected source-reference identity.
- `git diff --check` reported no whitespace errors; Git emitted existing
  mixed-line-ending warnings for the dirty working tree.
- Active goal SHA remained unchanged. No provider request, model generation,
  LoRA fit, sealed split access or SubRoute mutation occurred.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\iter147-typed-compact-context.json` | 3,873 | `D9FF615D13BAF01ECD17796AD73A0A10DFD6DE0168064356722BD92FA97EDC6D` |
| `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\iter148-typed-context-prune.json` | 4,752 | `2335A3987DBB395E6250E7F86987C9F12333EEF86789BEC515FB5EB8020875BB` |

Key source identities at report time:

| Source | SHA-256 |
|---|---|
| `src/wrench_harness/context.py` | `E5A04EB7BF300CA98F4BA53C47CC8C649325DACE984533928AF21929172EBC0B` |
| `src/wrench_harness/prompt_compiler.py` | `BBF3D1F8A7698807E87EE997429FC1BCF3B6D5A65E51CE91E282294DBE62B213` |
| `src/wrench_harness/e0_context_pipeline.py` | `D329E1ABB4C584F6B1E99E1ACDB29D911B3677345B9316D7DCE224A86BC753B5` |
| `examples/gateway_context_mvp/run_local_model_mvp.py` | `9508DCBC00C66B6543C9F5F82BB2B33053F5C7BDAFA90F3EE86C942F71F8B9C8` |
| `tools/measure_gateway_compact_context_iter147.py` | `B30288392163AB8D5928E1C33EAF64E13112875292E3F726C12130D70448C6F3` |
| `tools/measure_gateway_context_prune_iter148.py` | `E3073E88689A1FB85E1F77B8C2FDCED222EDDF11A8C9D1D8B86930DCFC03F35F` |

## Limits and next action

These are input-token counts on three synthetic lookup prompts. They do not
measure answer correctness, prompt-injection resistance in model behavior,
frontier calls, full-lifecycle frontier-token savings, cost, latency,
all-day coding, or LoRA benefit. The results cannot establish the 95/95
product gates. The no-warning arm relies on a task system instruction and is
diagnostic only. The quote-segment arm uses declared quote annotations to
choose evidence, so it needs a separately declared, answer-blind retrieval
rule before it can be treated as an implementation candidate.

Next, evaluate a deterministic source-span retrieval/pruning rule on held-out
synthetic coding tasks, then run the retained compact format through the local
answer verifier and injection fixtures. Preserve the exact segment-to-source
map and charge any recovery fetch. Resume the state-aware compaction and
mechanical-work engineering track separately from this tokenizer ablation.
