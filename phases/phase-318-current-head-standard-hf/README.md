# Phase 318: standard Hugging Face loader boundary

The current candidate was checked in an isolated runtime built from
`requirements/runtime.txt` with Transformers `5.17.0` and Hugging Face Hub
`1.32.0`.

The first attempt in the workstation's default Python used Transformers
`4.57.1` and correctly stopped at the repository minimum of `5.17.0`. The
isolated runtime then exposed a verifier bug: Transformers 5.17 removed the
private `AutoModelForImageTextToText._model_mapping` attribute that the old
checker used. The checker now validates the stable local config architecture
list instead.

## Result

- `AutoConfig` resolved `Qwen3_5MoeConfig` and
  `Qwen3_5MoeForConditionalGeneration`.
- `AutoTokenizer` loaded from local files.
- Hybrid standard HF config and tokenizer check passed.
- Native tokenizer context check passed with the advertised 4M limit.
- Full weight load was not attempted because the isolated environment has no
  PyTorch. This is intentionally not reported as a weight-load or generation
  pass.
- The full project regression after the verifier fix passed `194` tests with
  `0` failures and `18` warnings.

The package now has a current, tested standard HF metadata and tokenizer path.
The remaining standard-loader evidence is actual tensor loading and forward
generation with a compatible PyTorch or backend runtime. Dense-native 4M
quality remains unverified.
