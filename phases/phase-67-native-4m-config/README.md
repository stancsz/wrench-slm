# Phase 67: native 4M context stretch candidate

This phase prepares the 4M configuration stretch from the same Wrench 8E BF16
metadata. It is not a runtime or quality pass. The candidate uses
`max_position_embeddings=4000000` and a YaRN factor of
`4000000 / 262144` while leaving model weights unchanged.

Native 4M may be enabled only if a direct serving request reports the full
model-side prompt length, keeps recent intent available, retrieves old lookup
evidence correctly, and meets the frozen prefill, memory, throughput, and
failure budget. A larger number in `config.json` is not evidence by itself.
