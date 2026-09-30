# Iteration 062: IID power floor calibration

Timestamp: 2026-09-28 03:10 UTC (2026-09-27 America/Edmonton)

## Host gate

The most recent sample in this continuation measured 2,635.9 / 32,701.8 MiB
free RAM (8.06%), 15,246 / 16,311 MiB free VRAM on the RTX 5060 Ti, and
140.77 GB free on C:. The process query found no Wrench training, inference,
or benchmark process. RAM remains below the 10% operating floor, so no model
workload or delegation ran.

Storage was `WITHIN_LIMIT` at 10,991,252,665 bytes actual and 8,103,000 bytes
in active reservations before this 100,000-byte documentation reservation.
The reservation is `WRENCH-95-5-POWER-CALIBRATION-ITER062-20260927` and must
be released after accounting for this report.

## Exact IID power illustration

The product-proof design specifies five primary one-sided bounds and controls
family-wise alpha at 0.05. To give one usable planning floor for a binary
adverse-rate endpoint, allocate alpha 0.01 to that endpoint and assume the
true adverse rate is 2%. For each `n`, choose the largest `k` whose exact
one-sided Clopper-Pearson upper bound is at most 5%, then calculate the chance
of observing at most `k` adverse outcomes when `p=0.02`.

| Independent episodes | Maximum adverse outcomes | One-sided upper bound at alpha 0.01 | Power if true rate is 2% |
| ---: | ---: | ---: | ---: |
| 397 | 9 | 4.6731379% | 72.5369% |
| 398 | 10 | 4.9971385% | 82.1871% |

This makes 398 the first IID sample at this alternative with at least 80%
power under that single-endpoint acceptance rule. For comparison, the existing
proof design's `n=234`, `k=6` calculation at alpha 0.05 has a 4.9978391% upper
bound and 80.9139% power when the true adverse rate is 2%.

The calculation solves `P[X <= k | n, p_upper] = alpha` for the exact upper
bound, then evaluates `P[X <= k | n, p=0.02]`. It is not a powered sample
size for Wrench's full objective. It does not address correlated repository,
task-family, or workday episodes; paired frontier-only success retention; or
the continuous token and all-in cost ratios. Those endpoints and family-wise
control may require substantially more data. The product-proof design
correctly leaves final enrollment unadmitted until the target workload frame,
cluster counts, and endpoint-specific power analysis are frozen.

The current 128-case synthetic screen spans only a small set of synthetic task
families and remains mechanics evidence. It cannot establish representative
95/5 completion, 95% frontier-token savings, 95% lower all-in cost, or
all-day engineering.

No tests, model runtime, inference, training, provider request, or delegated
job ran in this iteration.
