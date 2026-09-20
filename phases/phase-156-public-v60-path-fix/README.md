# Phase 156: Public v60 copy-paste path fix

Date: 2026-09-20

## Purpose

Fix the materializer's direct Python worker example. The previous generated
README replaced only a path prefix and could produce a duplicated
`NVFP4-native4M` suffix. The materializer now replaces the complete canonical
package path.

## Evidence

- Targeted materializer regression: `5 passed`.
- Full repository regression: `146 passed, 14 warnings in 19.29s`.
- v60 structural package validation: `PASS_STRUCTURAL_PACKAGE` with zero
  errors.
- v60 downloaded-package 4M mechanical route:
  `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`, `16.171 ms`, `model_calls=0`.
- Fresh Hub download has no duplicated worker path and has the correct
  `WrenchWorker.from_pretrained` path.
- Fresh Hub download retains process-tree cleanup, serial expert loading, and
  native direct-input configuration.
- Public Hub revision:
  `6eab44cd8c41b24de4c424b524cba670a1f3713b`.

## Boundary

This is a packaging usability repair. It does not prove native 2M or 4M
generation, retrieval quality, MiniMax parity, GGUF compatibility, or
production readiness.
