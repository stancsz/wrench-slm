# Phase 132: fresh v44 220-case prompt-complete replay

This replay runs the current v44 portable package, including the newly
published package-local API runtime, against the derived executable
mechanical contract. It does not alter the historical 220-case fixture.

## Result

- Cases: 220.
- Eligible cases: 120.
- Outcome matches: 220/220.
- Exact eligible proposals: 120/120.
- Mechanical fast paths: 220/220.
- Model calls: 0.
- Prohibited accepts: 0.
- Transport/runtime abstentions: 0.
- Median latency: 0.594 ms.
- p95 latency: 42.204 ms.
- Mean latency: 6.908 ms.

The package therefore preserves the prompt-complete mechanical contract while
also accepting the raw 4M package-local Ollama-shaped request from Phase 131.
This is the strongest current evidence for fast practical work and zero-token
local execution. It is not native dense 4M retrieval quality, MiniMax parity,
or the family-disjoint production workflow gate.

## Evidence

- Contract cases SHA-256:
  `72DFD13DD9D3607207BB23E139D1581CFBB23E25A390EAF453225DB3CDB8EF053`.
- Receipt SHA-256:
  `9BD2E4796D8722807BB23E139D1581CFBB23E25A390EAF453225DB3CDB8EF053`.
- Runtime: `Wrench-4B-Qwen3.6-8E-NVFP4-native4M-portable-v44-ollama-api`.

