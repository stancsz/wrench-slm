# Phase 152: independent MiniMax-worker score replay

This phase reruns the checked-in scoring function against the two existing
220-case diagnostic trace manifests. It does not call MiniMax, load a model,
execute proposals, or alter the evaluation inputs.

Results:

- Complete-patch diagnostic: `QUALITY_GATE_OPEN`, 220 traces, 120 eligible
  traces, `0.8546684503519975` weighted frontier-token coverage, `1.0` net
  frontier-token savings, teacher non-inferiority passed, zero prohibited
  accepts, and zero unexpected mutations.
- Canonical v5 diagnostic: `QUALITY_GATE_OPEN`, 220 traces,
  `0.5091198427476598` weighted frontier-token coverage,
  `0.5966536852733304` net savings, zero prohibited accepts, and zero
  unexpected mutations.

The complete-patch result is closer to the 90% coverage target but still below
it. The canonical v5 result is materially below both the 90% coverage and 95%
savings targets. Neither is a release or production pass.
