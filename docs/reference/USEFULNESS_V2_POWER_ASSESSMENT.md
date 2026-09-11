# Usefulness V2 family-level power assessment

Updated: 2026-09-10

Status: EXPLORATORY INCONCLUSIVE. No paid comparison is authorized by this
assessment.

## Question

The workflow protocol uses wording families as the uncertainty unit and
compares the local arm against two comparators. The current V2 evaluation has
120 families and five instances per family. This document checks whether the
declared all-success fallback can support the two-percentage-point quality
margin before any cloud budget is spent.

The reproducible calculation is in
`scripts/pilot_power_v2.py`; its receipt is
`artifacts/model-release/usefulness-v2-power-assessment.json`.

## Observed design limits

The existing analyzer uses a 5% all-success bound separately for each
comparison. With 120 families, its exact fallback is:

```text
0.05 ** (1 / 120) - 1 = -0.0246554
```

That is below the declared `-0.02` noninferiority margin even if every family
succeeds. The two separate 95% bounds also do not provide a prospective 95%
simultaneous guarantee for both comparisons.

Using a Bonferroni allocation of family-wise alpha 0.05 across two comparisons
uses alpha 0.025 per comparison. At 120 families the corresponding fallback is
`-0.0302730`, which is more conservative and also fails the margin.

The calculation reports the following feasible balanced design:

| Design | Families | Cases at 5 per family | Per-comparison alpha | All-success lower bound | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Current V2 | 120 | 600 | 0.025 for simultaneous coverage | -0.0302730 | Does not support margin |
| Minimum unbalanced | 183 | 915 | 0.025 | -0.0200 or better | Meets boundary calculation |
| Balanced prospective | 198 | 990 | 0.025 | -0.0184582 | Meets boundary calculation |

The 198-family design is divisible by both 11 task kinds and two languages,
giving 18 families per kind and 99 families per language. It provides at least
95% family-wise coverage by the Bonferroni bound. This is a boundary
calculation, not power to detect a nonzero effect size.

## Decision and use

The existing 120-family V2 result remains an exploratory local result. Do not
change its rule after seeing the scores, reinterpret five instances as five
independent families, or use the current result to authorize a paid workflow.

Before a future paid comparison, freeze one of these choices in the protocol:

1. use at least 198 new families and 990 cases, with the two-comparison
   Bonferroni rule and the existing quality margin; or
2. explicitly label the comparison exploratory and INCONCLUSIVE, with no GO
   claim based on the underpowered uncertainty bound.

The design does not solve the separate requirements for independent authoring,
ancestor-template coverage, out-of-contract stress cases, local runtime
benchmarking, or candidate quality gates. Those remain blocking requirements.
