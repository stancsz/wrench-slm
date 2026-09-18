# Phase 12: architecture-aware pruning-source validator

This phase adds `tools/validate_pruning_source.py`. It is a metadata-only gate
that checks the Qwen3.6 MoE architecture, requires the official safetensors
index and expected unquantized size, verifies mapped shards exist, and rejects
FTW or quantization metadata. It never loads, slices, or rewrites weights.

The validator is deliberately strict: a checkpoint must be proven eligible
before any future router profiling or structural-pruning code is allowed to
run. The unit suite also proves a representative packed FTW package is
rejected.
