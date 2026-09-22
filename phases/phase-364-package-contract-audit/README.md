# Phase 364: Package contract audit

Date: 2026-09-21

Status: `PASS_HYBRID_PACKAGE_CONTRACT_PARTIAL_NATIVE`

The locally available release candidate package manifest records the intended
hybrid production lane:

- Verified parameters: `3,881,244,016`, below the hard ceiling of
  `4,250,000,000` by `368,755,984` parameters.
- Raw input surface: `4,000,000` tokens, with over-limit requests rejected.
- Default effective working context: `64,000` tokens, split into a `48,000`
  token hot context and a `16,000` token reference card.
- First model-side stage: `pruner + cherrypicker`, using
  `mapreduce_dynamic_native` and raw-payload hash binding.
- Mechanical lookup route: bundled and model-call-free.

The manifest also keeps the release boundary honest. Dense native 2M attention
is an optional target but is not verified in this package. Ollama MLX import and
4M metadata are recorded, but native Ollama generation quality failed on the
validation host. vLLM requires a registered Wrench architecture and GGUF is
unverified.

This audit supports the 4M hybrid model-local product lane and the sub-4.25B
constraint. It does not promote dense-native decoder quality, Ollama native
generation, vLLM support, or production readiness.
