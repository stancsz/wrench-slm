# Phase 155: Native process-tree cleanup and public v59 package

Date: 2026-09-20

## Purpose

Make the public portable package safe to retry when native FreeToken startup
fails on a Windows host with insufficient GPU memory or commit/pagefile
capacity. The generated launcher now terminates the complete native process
tree with `taskkill.exe /T /F` in its `finally` block.

## Evidence

- Full repository regression: `146 passed, 14 warnings in 20.85s`.
- v59 structural package validation: `PASS_STRUCTURAL_PACKAGE` with zero
  errors.
- v59 downloaded-package 4M mechanical route:
  `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`, `16.051 ms`, `model_calls=0`.
- Real v59 launcher smoke on `NativePort=28206` and `Port=28906` exited with
  code 1 because the current host had only about 798 MiB of free GPU memory;
  FreeToken raised CUDA out of memory while building rotary embeddings.
- Post-smoke inspection found no listener on ports 28206 or 28906 and no
  process command line containing either test port.
- Fresh Hub download verified the published launcher contains process-tree
  cleanup, serial expert loading, and one-thread BLAS settings.
- Public Hub revision:
  `5456c8942efc14950fec0d2ce57f73eaa9a02c5c`.

## Boundary

This phase proves portable packaging, cleanup behavior, and the mechanical 4M
route. It does not prove native 2M or 4M generation, retrieval quality,
MiniMax parity, GGUF compatibility, or production readiness. Native generation
remains blocked on this host's GPU and Windows commit/pagefile state.
