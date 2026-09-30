# Iteration 084: primary-gate power sensitivity

Date: 2026-09-28 (America/Edmonton)  
Job ID: `WRENCH-GATE-POWER-SENSITIVITY-ITER084-20260928`  
Status: non-binding IID sensitivity analysis; not a product sample-size approval  
Goal: [Wrench gateway LoRA and cost-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)

## Purpose

The [product proof design](product-proof-design-20260927.md) requires a
preregistered simulation of at least 80% joint power across five gates,
including repository/workday clustering, paired success retention, token and
cost ratios, and multiplicity. It correctly says the IID calculations are
not the product sample size. This iteration makes the binary-gate sensitivity
reproducible and quantifies why the planned 50-episode workday floor and the
128-case synthetic held-out split cannot establish the population claims.

## Exact binary-gate calculation

For one binary adverse-event endpoint, let `q` be its true rate and `n` the
number of independent episodes. A local-completion endpoint can be written as
an adverse failure rate `q = 1 - local completion`; frontier episode use is
already an adverse-event rate. The project threshold is `q0 = 0.05`.

The five primary claims use a one-sided per-endpoint alpha of 0.01 under the
preregistered Bonferroni plan. For each `n`, define `k*` as the largest
observed adverse count satisfying:

```text
BinomialCDF(k*; n, q0 = 0.05) <= alpha = 0.01
```

The exact marginal power at an alternative `q1` is:

```text
BinomialCDF(k*; n, q1)
```

Searching integer `n` and `k*` gives:

| True adverse rate `q1` | Equivalent local completion (if failures) | Minimum `n` for 80% marginal power | Max adverse count at that `n` | Minimum `n` for 95.635% marginal power | Max adverse count at that `n` |
|---:|---:|---:|---:|---:|---:|
| 1% | 99% | 198 | 3 | 288 | 6 |
| 2% | 98% | 398 | 10 | 606 | 18 |
| 3% | 97% | 997 | 34 | 1,580 | 59 |

At `q1 = 2%`, the exact power is 82.19% at `n = 398` and 96.10% at
`n = 606`. The 95.635% column is the equal-gate illustration
`0.80^(1/5)`: if five binary gates were independent and had equal marginal
power, that would yield 80% joint power. The actual product gates are not five
identical independent Bernoulli endpoints, so these figures are a planning
sensitivity only. At the null boundary `q = 5%`, the chance of passing a
one-sided alpha-0.01 test is at most 1%; a study must predeclare a plausible
true rate below the boundary to design for useful power.

## Denominator and endpoint limitations

The success-retention claim is conditional on episodes that pass in the
frontier-only arm. Its denominator is not the total episode count. As one
illustration, if the frontier-only pass rate were 80%, an IID sample of 781
episodes would have about a 95.64% chance of containing at least 606
frontier-only successes. This only sizes that conditional binary denominator
under the stated hypothetical rate; it does not account for paired outcome
correlation or repository/workday clusters.

The token and all-in cost claims are ratios of paired weighted totals, not
Bernoulli events. Their power depends on paired task-level token/cost
distributions, correlations, heavy tails, cache treatment, zero denominators,
local-compute measurement, and cluster layout. No matched paid-provider usage
pair exists, and this iteration did not fabricate such a distribution. Their
sample size cannot be inferred from episode counts or the binary table.

The existing synthetic label split has only 128 cases per split and is
mechanics-only. Even under IID assumptions it is below the 198-episode floor
for an 80%-powered single binary gate when the true adverse rate is 1%, and
well below the 398 cases for a 2% alternative at alpha 0.01. The 50-episode
minimum across ten workday sessions is an operational repeatability gate, not
a powered population sample.

## What is still needed before enrollment

1. Freeze the target population, task-family weights, repository and time
   groups, session sampling, and eligibility rules.
2. Obtain a separately permitted development pilot with complete task,
   paired pass, route, token, price, local compute, and rescue receipts. Do
   not reuse sealed final data to tune the alternative or estimate variance.
3. Estimate the paired outcome and token/cost distributions from that pilot,
   preserving the intended repository/workday cluster design.
4. Simulate the complete analysis at every null boundary and at declared
   plausible alternatives; verify interval coverage and at least 80% joint
   power across all five gates. Freeze the analysis code and stopping rule
   before final enrollment.

Until then, report any run as a pilot or mechanics result. Do not label 398,
606, 781, the synthetic split size, or the ten-session gate as the final
product sample size.

## Scope and reproducibility

The table is reproducible with the standard-library calculator
[`tools/gate_power_sensitivity.py`](../../../tools/gate_power_sensitivity.py):
run `python -B tools/gate_power_sensitivity.py` from the repository root. Its
deterministic JSON output reproduced all six `(n, max adverse count)` pairs
above and the `n = 781` retention-denominator illustration. The script writes
only to stdout.

The calculation used the exact lower-tail binomial recurrence for integer
counts, `q0 = 0.05`, per-endpoint `alpha = 0.01`, alternatives `q1` in
`{0.01, 0.02, 0.03}`, and target marginal power 0.80 or
`0.80^(1/5) = 0.9563525`. For the retention illustration it additionally
assumed an 80% independent frontier-only pass probability and required a
95.635% chance to observe at least 606 such successes.

No model was loaded, trained, or inferred. No provider call, held-out payload
read, test run, or change to the Fit-03 protocol or current goal was made.
