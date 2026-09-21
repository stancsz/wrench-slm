# Phase 235: portable hybrid package v93

Status: `PASS_PORTABLE_HYBRID_PACKAGE`

The pinned 3.88B BF16 Safetensors candidate was materialized into
`D:\models\Wrench-Qwen3.6-8expert-BF16-hybrid-v93` using hard links for the
immutable weight shards. The directory bundles the Wrench worker, verifier,
mechanical toolbelt, deterministic MapReduce prefill, tokenizer hook, server
entrypoint, and runtime profile.

Structural validation passed with zero errors. The package reports:

- verified parameters: `3,881,244,016`;
- hard parameter ceiling: `4,250,000,000`;
- logical raw input limit: `4,000,000`;
- effective working context: `64,000`;
- hot context: `48,000`;
- reference cards: `16,000`;
- first model-side stage: `first_model_side_pruner_cherrypicker`;
- dense-native gate: conditional and optional.

A fresh package-local 4M mechanical route accepted the request in 28.935 ms,
with zero model calls. This proves the copy-pasteable hybrid runtime surface,
not dense-native attention quality or learned MiniMax parity.

Evidence: `validation.json` and `4m-route.json`.
