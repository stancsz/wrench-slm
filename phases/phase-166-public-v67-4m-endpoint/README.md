# Phase 166: public v67 4M endpoint intake

The freshly materialized v67 package was exercised directly through its
bundled model-local HTTP server. The request body contained a 4,000,000-token
estimated payload. This is the package endpoint itself, not a separate API
gateway.

## Receipts

- direct downloaded-package worker route: `PASS_PUBLIC_PACKAGE_4M_MECHANICAL_ROUTE`
- worker route elapsed: 16.484 ms
- worker route model calls: 0
- worker route raw payload characters: 35,199,491
- HTTP model-local server route: `PASS_MODEL_LOCAL_SERVER_4M`
- HTTP status: 200
- HTTP request elapsed: 145.594 ms
- HTTP request bytes: 32,500,168
- HTTP raw payload characters: 32,000,075
- reported prompt tokens: 4,000,010
- reported completion tokens: 1
- reported total tokens: 4,000,011

## Boundary

The package accepts and accounts for the complete 4M logical request, then
uses the embedded deterministic MapReduce route. This proves direct package
intake and the hybrid fast path. It does not prove that a native backend uses
dense attention over all 4M tokens, nor does it prove MiniMax parity or final
production enablement.
