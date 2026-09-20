# Phase 123: native launcher root and full 220 regression

This phase validates the portable package after adding an explicit
`-AllowedRoot` parameter to the FreeToken launcher.

## Change

The native embedded route now receives `WRENCH_ALLOWED_ROOT`. Mechanical patch
proposals are generated against that root and are checked by the bundled
read-only verifier before the no-model response is returned. The verifier never
applies a patch.

## Evidence

The v41 package was materialized from the NVFP4 native-4M artifact and passed
the structural package validator:

- receipt: `v41-package-validation.json`
- status: `PASS_STRUCTURAL_PACKAGE`
- config position capacity: 4,000,000
- safetensor shards: 2

The real FreeToken endpoint was started with:

```powershell
.\serve_freetoken.ps1 -Port 28934 `
  -AllowedRoot C:\path\to\phase-120-executable-mechanical-contract\fixture `
  -FastHistory -FastHistoryKeepTokens 64000
```

After the endpoint reported `API server is ready to serve`, the complete
prompt-complete 220-case contract passed:

- 220/220 outcome matches
- 120/120 exact eligible proposals
- 220/220 native embedded mechanical fast paths
- 0 model calls
- 0 prohibited accepts
- 0 transport/runtime abstentions
- median 0.544 ms
- p95 39.022 ms
- mean 6.737 ms

Receipt: `full-220-v41-native-allowed-root-ready.json`.

The first v41 attempt began before FreeToken finished loading its expert bank
and produced 503 responses. That cold-start observation is retained in
`full-220-v41-native-allowed-root.json` and is not used as the quality result.

## Boundary

This proves package-local mechanical semantics and the native endpoint route.
It does not prove MiniMax parity, native 4M retrieval quality, or the approved
matched real-workflow token-savings gate.
