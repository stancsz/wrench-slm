# Phase 333: Standard HF BF16 candidate

Status: `PASS_STANDARD_HF_CONFIG_TOKENIZER_NATIVE`, diagnostic candidate only.

The existing BF16 checkpoint was materialized with the current Wrench runtime
into:

```text
D:\models\_wrench-standard-release-candidate-bbc680f
```

This candidate has the same verified parameter count as the NVFP4 package,
`3,881,244,016`, but uses ordinary BF16 Safetensors rather than ModelOpt
NVFP4-packed tensors.

## Evidence

- Structural package validation: passed with zero errors.
- Transformers `5.17.0` full-weight load: passed, model class
  `Qwen3_5MoeForConditionalGeneration`.
- Loaded parameter count: `3,881,244,016`.
- Full weight load elapsed time: `7,514.245 ms` in the package verifier.
- Model-local 4M hybrid route: passed in `31.24 ms`, zero model calls.
- OpenCode and DeepSeek Harness: exit `0`, structured read observed.
- Claude Code: exit `0`, structured read observed.
- Package size: `7,910,979,763` bytes, about `7.368 GiB`.

The separate bounded GPU generation smoke also loaded the same BF16 weights on
the RTX 5070 Ti and generated four tokens. It kept about `7.96 GiB` free after
load and `7.75 GiB` free after generation, above the 10 percent VRAM reserve.
The short output was `"< : c >"`; this is load and generation evidence only,
not a quality or MiniMax parity pass.

## Decision

The current NVFP4 package remains the default fast and smaller candidate at
about `3.189 GiB`, with FreeToken ModelOpt as its native weight backend. The
BF16 candidate proves that a standard Transformers Safetensors lane is
technically available, but its larger download and unverified task quality do
not justify replacing the smaller package yet.

This phase does not prove dense-native 4M quality, independent RTX 5060 Ti
verification, learned MiniMax parity, or production enablement.
