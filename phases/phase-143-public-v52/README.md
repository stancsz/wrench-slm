# Phase 143: public v52 embedded native handoff

The portable package now includes the deterministic staged prefill in the
package-local server path before forwarding ambiguous requests to the internal
native backend.

## Evidence

- structural package validation: `PASS_STRUCTURAL_PACKAGE`
- downloaded-package 4M mechanical route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`
- package route latency: `18.93 ms`
- model calls on mechanical route: `0`
- local 4M reducer stress: `PASS_EMBEDDED_MONSTER_PREFILL`
- local 4M reducer latency: `621.756 ms`
- public Hub revision: `7431730327e4564a348a9c8cd04a8d437dd3bc67`
- weights changed: no
- fresh Hub download hash verification: passed for README, distribution docs,
  and `wrench_runtime/server.py`

This closes the previous packaging gap: raw 4M input can be accepted by the
package and reduced before native handoff. The 621.756 ms reducer measurement
does not pass the requested sub-100-ms map-reduce target. Native dense 4M
retrieval quality, MiniMax parity, stock Ollama or GGUF loading, and production
readiness remain unverified.
