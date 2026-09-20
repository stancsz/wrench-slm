# Phase 84: standard Hugging Face loader

Status: `PASS_STANDARD_HF_CONFIG_TOKENIZER`

The public model snapshot and the local v4 portable directory were checked in
an isolated Transformers 5.17.0 environment. `AutoConfig` resolves the
Qwen3.5 MoE architecture to `Qwen3_5MoeForConditionalGeneration`, and
`AutoTokenizer` resolves the bundled `WrenchTokenizer` with
`model_max_length=4,000,000`.

Receipts:

- `standard-hf-load.json` checks the local portable package.
- `standard-hf-load-public-snapshot.json` checks a fresh public Hub snapshot
  containing the config, tokenizer, and bundled runtime files.

This phase does not load the 4B tensors or claim generation quality. Full
weight generation, vLLM/Ollama adapters, native retrieval quality, and the
MiniMax matched-workflow gates remain separate requirements.
