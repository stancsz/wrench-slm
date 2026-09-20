# Phase 129: top-k=4 direct-model quality probe

This phase compares the weight-identical top-k=4 NVFP4 variant with and
without the bundled deterministic route on the complete historical 220-case
fixture. It is a diagnostic quality probe, not a release gate or a matched
real-workflow result.

## Results

| Mode | Outcome matches | Exact eligible accepts | Prohibited accepts | Median | p95 | Model calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Embedded mechanical route | 200/220 | 82/120 | 0 | 0.285 ms | 56.005 ms | 0 |
| Direct model, route disabled | 62/220 | 4/120 | 6 | 415.166 ms | 1560.488 ms | endpoint metadata unavailable |

A short direct-generation smoke produced a schema-valid read proposal in
approximately 88 ms, but the complete direct replay produced repeated JSON,
malformed objects, invented paths, and six prohibited accepts. The direct
top-k=4 variant is therefore rejected for publication and router promotion.

The embedded route remains the useful path for the bounded mechanical
portfolio. Its result does not prove native dense 4M retrieval quality,
MiniMax parity, or the approved family-disjoint workflow gate.

## Receipts

- `canonical-220-v2.json`: mechanical route enabled.
- `canonical-220-direct-model.json`: mechanical route disabled.
- Cases SHA-256: `54D06DFF69C2A330FBBA5ED13BA22817C287CB7EC384A59458EB4F5E291BB45A`.
- Mechanical receipt SHA-256:
  `79DC42D9D628CEFC457DBEEB3D7A85120C79049684DB5F00F34DE6CC51A0134E`.
- Direct-model receipt SHA-256:
  `CD6CE1A79E6F80DF8DE04932987645140BBB7D8435A7EB554D206AD7564DE4FD`.

