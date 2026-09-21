# Phase 273: 5060TI current package workflow evidence

Date: 2026-09-21

## Confirmed worker results

The connected worker is `DESKTOP-KET1SKP` with an NVIDIA GeForce RTX 5060 Ti.
The package preflight had already verified the two NVFP4 shards and preserved
more than the required host reserve. The worker reported 50.18% free RAM and
93.92% free VRAM before and after the preflight.

The package-local HTTP endpoint accepted a direct nominal 4,000,000-token
request without an external API gateway. The request contained 31,997,963 raw
characters and completed in 439.327 ms end to end. This is direct model-local
logical intake plus the package's deterministic reduction path.

The installed DeepSeek Harness client completed an isolated read-only smoke
against the package and returned the first heading from the workspace.

The separate 220-case replay completed all 220 traces with status
`QUALITY_GATE_OPEN`. The remote agent was still validating hashes, safety
counters, and resource reserves when this receipt was recorded, so no final
quality or parity claim is made from that replay yet.

## Boundaries

- OpenCode is not installed on the 5060TI host, so there is no remote OpenCode
  result. OpenCode remains verified on the local development host.
- The worker checkout was dirty at `bcf80d9` while `origin/main` was at
  `08daf09`; the worker correctly did not overwrite local changes. This is
  independent package evidence, not a current-source 08daf09 claim.
- `QUALITY_GATE_OPEN` is not `PASS_MECHANICAL_WORKER`.
- The result does not prove learned MiniMax parity, dense-native attention
  quality, or production enablement.

## Next evidence

Collect the completed replay evaluation path, trace manifest hash, exact safety
counters, and resource snapshot after the remote worker returns its terminal
receipt. Keep the package and client traces outside the source repository.
