# Phase 228: fresh real LoRA development rerun

The current fused rank-8 LoRA checkpoint was evaluated again with the real
CUDA Transformers generation path on all 44 development rows. This rerun did
not use the mechanical shortcut and did not read the sealed final split.

Results:

- outcome matches: 30/44
- exact target matches: 16/44
- verified accepts: 18/44
- median generation latency: 3,768.530 ms
- p95 generation latency: 8,688.215 ms
- device: `cuda:0`

The 14 outcome misses were concentrated in long path copying, patch diff
copying, and health transport fixture behavior. Several patch outputs were
schema-valid but semantically different from the target, while path copying
produced malformed or truncated paths. The learned model therefore remains a
fallback aid, not the owner of routine mechanical work.

This receipt is development-only. It does not prove family-disjoint quality,
MiniMax parity, 4M generation quality, or production readiness.
