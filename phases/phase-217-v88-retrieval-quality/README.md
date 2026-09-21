# Phase 217: v88 2M/4M retrieval quality

Date: 2026-09-20

The v88 package-local worker was tested against unique old-reference needles
at 1%, 50%, and 99% positions in both 2M and 4M payloads. Each of the six
placements ran three repetitions, for 18 total cases.

- exact proposals: `18/18`;
- backend: `embedded-mechanical` for every case;
- route: `reference_lookup` for every case;
- model calls: `0`;
- first-layer stage: `mechanical_fast_pruner_cherrypicker` for all 18;
- raw payload hash binding: `true` for all 18;
- 2M retrieval p50 / empirical p95: `17.870 ms` / `20.956 ms`;
- 4M retrieval p50 / empirical p95: `32.560 ms` / `40.772 ms`;
- all-case p50 / empirical p95: `20.956 ms` / `40.772 ms`.

This is strong evidence for reference-only lookup quality on the hybrid path.
It is not dense-native attention quality, learned MiniMax parity, or a
family-disjoint production approval.
