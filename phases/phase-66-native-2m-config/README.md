# Phase 66: native 2M context candidate configuration

This phase prepares a non-destructive 2M context configuration candidate from
the verified Wrench 8E BF16 checkpoint metadata. It does not copy or modify
weights, and it does not claim long-context quality.

The source checkpoint reports 262,144 positional capacity. The candidate
config sets `text_config.max_position_embeddings` to 2,000,000 and uses a YaRN
factor of `2000000 / 262144`. This is a runtime experiment input only. A
config change cannot prove that the model learned to retrieve information at
the beginning, middle, and end of a 2M sequence.

The installed local Transformers runtime does not expose
`Qwen3_5MoeForConditionalGeneration`, and vLLM is not installed in this
environment. Therefore this phase stops at a config candidate. The next
required evidence is a complete standard Safetensors artifact loaded by a
long-context-capable runtime, followed by the direct native probe and quality
tests.

Receipts:

- `receipt.json`: source and candidate hashes plus the explicit non-claim;
- `runtime-check.json`: current runtime readiness check;
- `config.json`: candidate config without model weights.
