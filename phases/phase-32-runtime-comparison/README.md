# Phase 32: matched runtime comparison

Phase 32 compares the latest calibrated 8-expert and 16-expert text-only FTW
artifacts with the original Qwen3.6-35B-A3B NVFP4 teacher on the same corrected
28-case fixture. The source receipts are the Phase 30 and Phase 31 runtime
receipts, so this phase does not introduce a new prompt split or tuning pass.

Observed wall time is measured per request. The reported p95 uses the
nearest-rank definition, with the request count shown in the receipt. These
numbers are local synthetic-fixture diagnostics. They do not establish
throughput, production latency, workflow value, or release readiness.

| Runtime | Cases | Mean wall time | p95 wall time | Mean completion tokens | Mean total tokens | Total elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 8E calibrated FTW | 28 | 6.076 s | 11.275 s | 51.1 | 176.7 | 195.495 s |
| 16E calibrated FTW | 28 | 4.271 s | 11.357 s | 34.5 | 160.0 | 145.035 s |
| 35B teacher NVFP4 | 28 | 9.852 s | 17.398 s | 45.1 | 170.6 | 336.416 s |

The 16E receipt has the lowest mean wall time in this run, followed by 8E and
then the original teacher. The tail is still uneven, and the two pruned tiers
remain below the usefulness and human-approval gates recorded in `GOAL.md`.

