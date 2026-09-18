# Phase 47: guarded holdout runtime and token accounting

The Phase 45 compact and Phase 46 larger receipts were summarized on the same
14-case holdout. The compact 8E tier completed in 25.390 seconds with a mean
request time of 1,813.6 ms, nearest-rank p95 of 2,380.6 ms, and 4,542 total
reported tokens. The larger 16E tier completed in 30.621 seconds with a mean
request time of 2,187.2 ms, nearest-rank p95 of 3,262.0 ms, and 4,590 total
reported tokens.

The compact tier is faster on this fixture, while the larger tier accepts more
routine cases and matches more expected outcomes. These are paired synthetic
diagnostics, not paid-token savings or production latency evidence.
