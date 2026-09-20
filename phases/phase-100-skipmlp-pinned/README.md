# Phase 100: pinned native history MLP skip

This is an opt-in native serving diagnostic on top of the pinned 4M KV
geometry. It skips the expensive MoE MLP computation before token position
48,000 while retaining the recent suffix on the normal path.

## Matched probe

Both probes used the same v27 NVFP4 package, 4M `--num-tokens` capacity, auto
expert cache, direct 64K input, and `max_tokens=1`:

- no skip: `65,472` actual prompt tokens, no truncation, `23,108.787 ms`;
- `WRENCH_HISTORY_SKIP_MLP_BEFORE=48000`: `65,473` actual prompt tokens, no
  truncation, `17,004.096 ms`.

The optional profile is about `1.36x` faster in this one matched probe. It is
not enabled by the public launcher because this phase has not yet verified
long-context retrieval quality, proposal correctness, or MiniMax parity under
the skipped history path.
