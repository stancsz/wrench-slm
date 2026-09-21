# Phase 319: standard Hugging Face full-weight load boundary

This phase performed the stronger check that phase 318 had not yet performed:
loading all 693 safetensor shards through the standard Transformers path.
The candidate was loaded from `D:\models\_wrench-release-candidate-a8a75c3` in
an isolated environment with Transformers `5.17.0`, Hugging Face Hub `1.32.0`,
and CPU-only PyTorch `2.9.1`.

## Result

Status: `FAIL_STANDARD_HF_WEIGHT_LOAD`

- The config and tokenizer still resolved successfully.
- The loader recognized `Qwen3_5MoeForConditionalGeneration` and read all
  `693/693` weight files.
- Transformers reported that the package's `modelopt` quantization type is
  unsupported in this runtime and skipped that quantization path.
- The resulting packed NVFP4 tensors then failed multiple model shape checks.
  Examples included expert `gate_up_proj`, expert `down_proj`, linear-attention
  projections, and selected self-attention projections.
- `full_weight_load_verified` is `false`; no generation claim is made.
- The load attempt took `113528.289 ms` and did not violate the 10% host-memory
  reserve. This was a compatibility failure, not an out-of-memory result.

The verifier now catches this class of error and writes a structured failure
receipt instead of leaving only an exception trace. The package must not be
described as a normal `AutoModel.from_pretrained()` portable model until the
ModelOpt/NVFP4 runtime path is either embedded or the weights are exported to a
standard Transformers-compatible representation.

Evidence: `phase-319-current-head-standard-hf-load.json`.
