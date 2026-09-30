# Iteration 161: Qwen3.5-4B chat-template boundary diagnostic

- Job ID: `WRENCH-QWEN35-4B-TEMPLATE-BOUNDARY-DIAG-ITER161-20260928`
- Scope: read-only local tokenization of the pinned Qwen3.5-4B tokenizer over approved synthetic train/dev rows only; no model load, inference, optimizer, heldout payload, provider call, or output file from the diagnostic.
- Pinned model revision: `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- Tokenizer source was local with offline flags; `tokenizer.is_fast` was true.

## Findings

On `train-evidence_select-0043`, prompt and full chat serialization are an exact character prefix: prompt length 868 chars; full length 1,052. However, independent tokenization diverges at token index 245. The generation prompt ends with `<|im_start|>assistant\n<think>\n`; the full serialization continues `\n</think>\n\n{...}`. In the fully tokenized text, token index 245 spans character offsets `[867, 869)` and represents two newlines, crossing the prompt boundary at character 868. The next token is `</think>`. Therefore the source's equality assumption for independently tokenized prompt/full token-ID prefixes is invalid even though the serialized strings match.

A second bounded pass covered all 256 synthetic train and 64 synthetic dev rows. It found:

- 320/320 serialized full strings begin with their generation-prompt serialization.
- 320/320 contain exactly one token crossing the character boundary; both the prompt-side and continuation-side characters in every crossing token are whitespace.
- 0 crossing tokens include non-whitespace prompt or answer content.
- 0 assistant answers are missing from the full serialization after the boundary.
- 0 empty assistant target spans under an offset-based boundary rule.
- Full sequence maximum: 338 tokens, below the 512-token cap.
- With tokens whose start offset is before the character boundary masked, the remaining assistant/template target spans ranged from 45 to 74 tokens.

## Engineering implication

Build `input_ids` by tokenizing the **full serialized conversation once** with `return_offsets_mapping=True`. Set labels to `-100` for every token whose start offset is before the generation-prompt character boundary; supervise only tokens whose start is at or after the boundary. Fail closed if the tokenizer is not fast, offset mappings are invalid, the full serialization is not a character prefix extension, a crossing token contains non-whitespace characters on either side, sequence/target bounds fail, or the assistant answer is not present after the boundary. This avoids treating separately tokenized IDs as prefix-aligned and avoids training any token that includes prompt-side characters. The one cross-boundary newline token is masked in full.

This is a tokenizer boundary finding, not proof the adapter trains, learns the intended behavior, or improves Wrench utility. Attempt 02 remains failed and immutable. A code change requires a fresh trainer/protocol identity, independent review, and a unique attempt-03 preflight package.
