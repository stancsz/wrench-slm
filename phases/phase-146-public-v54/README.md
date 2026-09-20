# Phase 146: public v54 direct-input switch

The public package now exposes two honest modes. The default Ollama-compatible
package route stages raw context to the bounded working set. `-NativeDirectInput`
sets `WRENCH_NATIVE_DIRECT_INPUT=1`, makes the package server forward the raw
messages, and emits a hash-bound `native_direct_input` receipt.

## Evidence

- full repository regression: `146 passed, 14 warnings`
- structural package validation: `PASS_STRUCTURAL_PACKAGE`
- downloaded-package 4M mechanical route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`
- package route latency: `17.715 ms`
- mechanical model calls: `0`
- public Hub revision: `bec023ca041e7627ac85e5be29d01c5bfaf76a32`
- weights changed: no
- fresh Hub download hash verification: passed for all eight updated files

This makes native direct-input claims mechanically distinguishable from the
fast staged path. The native direct route still needs clean-GPU 2M and 4M
generation and retrieval-quality evidence. This phase does not claim GGUF,
stock Ollama, vLLM, MiniMax parity, or production readiness.
