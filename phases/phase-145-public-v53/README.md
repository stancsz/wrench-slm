# Phase 145: public v53 fast prefill package

The public portable package now includes the optimized deterministic prefill
and conservative old-reference lookup policy.

## Evidence

- full repository regression: `145 passed, 14 warnings`
- structural package validation: `PASS_STRUCTURAL_PACKAGE`
- downloaded-package 4M mechanical route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`
- package route latency: `25.521 ms`
- mechanical model calls: `0`
- standalone 4M reducer: `92.763 ms`
- package-server 4M raw-to-native handoff: `PASS_NATIVE_HANDOFF_STAGED_4M`
- raw input estimate: `3,999,942` tokens
- staged input estimate: `1,845` tokens
- server-side staging: `85.714 ms`
- public Hub revision: `9827766d5b5e33701f996a5cca34ad9255819bc5`
- weights changed: no
- fresh Hub download hash verification: passed for all seven updated files

The handoff probe uses a local protocol stub, so it proves package intake,
deterministic reduction, and forwarding shape. It does not prove native dense
4M retrieval quality, MiniMax parity, GGUF or stock Ollama loading, or
production readiness.
