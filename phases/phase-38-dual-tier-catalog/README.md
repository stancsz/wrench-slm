# Phase 38: dual-tier artifact catalog

The current external artifacts now form an explicit two-tier Wrench set:

- Compact safety tier: 8E, 3.188 GiB, 3,881,244,016 parameters.
- Larger utility tier: prior 16E, 3.718 GiB, 4,888,532,336 parameters.

The catalog also records the safety-calibrated 16E candidate. It is the same
3.718 GiB size, but its task acceptance fell from 8/20 to 6/20 while removing
the last prohibited accept. It is retained for future balanced calibration and
is not the recommended larger default.

The recommended split is therefore the safety-calibrated 8E pack for the
compact tier and the prior 16E pack for the more useful larger tier, both
behind the strict verifier and fallback path. This is an experimental artifact
selection, not a production enablement decision.

The mechanically generated catalog is `catalog.json`.

