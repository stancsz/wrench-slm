# Phase 168: bounded native expert-placement profiles

The portable launcher now exposes FreeToken's bounded expert-placement
controls while keeping the default profile unchanged. This supports the
production direction of MapReduce first, with native attention as an
optional path when the host has enough memory.

## Implementation

- `-MoeStrategy` accepts `offload`, `cpu`, `hybrid`, or `fused`.
- `-MoeCpuLayers` and `-MoeCpuThreads` can move or constrain expert work.
- `-MoeHybridMaxFetch` bounds hybrid expert fetches.
- The default remains `offload` with automatic expert-cache sizing.
- Native smoke readiness still gates the public package API, and the launcher
  kills the full native process tree on failure.

## Verification

- Targeted materializer and prefill tests: `18 passed`.
- v69 structural package validation: `PASS_STRUCTURAL_PACKAGE`.
- FreeToken help confirmed `cpu`, `hybrid`, CPU-layer, CPU-thread, and hybrid
  fetch controls.
- A controlled CPU-profile startup probe reached the native listener and
  parsed `moe_strategy='cpu'`, but the smoke request returned `503` because the
  current development host had only about `1.31 GiB` free GPU memory and CUDA
  could not allocate about `490 MiB`.
- The owned launcher process tree was terminated and the native ports were
  released in cleanup.

## Boundary

This phase proves launcher parameterization and failure cleanup. It does not
prove native dense 2M or 4M attention, native retrieval quality, MiniMax
parity, or production throughput. The release path remains the deterministic
MapReduce reducer with a 64K default effective working context. Native expert
placement is an optional runtime profile, not a prerequisite for the model's
4M input endpoint.
