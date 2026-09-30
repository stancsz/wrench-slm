#!/usr/bin/env python3
"""Reproduce IID gate-power sensitivity examples for the Wrench research report.

These calculations are illustrative only. They assume independent Bernoulli
outcomes, a one-sided exact binomial test, null adverse rate 5%, and per-endpoint
alpha 1%. They do not establish a product sample size or validate a model.
"""

from __future__ import annotations

import json
import math


NULL_ADVERSE_RATE = 0.05
ALPHA = 0.01
TARGET_POWERS = (0.80, 0.80 ** (1 / 5))
ADVERSE_RATES = (0.01, 0.02, 0.03)
MAX_N = 5_000


def binomial_cdf(k: int, n: int, p: float) -> float:
    """Return P[X <= k] using a stable recurrence for the small tail here."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    if p <= 0:
        return 1.0
    if p >= 1:
        return 0.0

    term = (1.0 - p) ** n
    total = term
    for x in range(k):
        term *= ((n - x) / (x + 1)) * (p / (1.0 - p))
        total += term
    return min(1.0, total)


def binomial_sf_at_least(k: int, n: int, p: float) -> float:
    """Return P[X >= k] by summing the upper tail from its first term."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0

    # Compute P[X=k] in log space, then recur upward to avoid underflow.
    log_term = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(p)
        + (n - k) * math.log1p(-p)
    )
    term = math.exp(log_term)
    total = term
    for x in range(k, n):
        term *= ((n - x) / (x + 1)) * (p / (1.0 - p))
        total += term
    return min(1.0, total)


def critical_max_adverse(
    n: int, null_rate: float = NULL_ADVERSE_RATE, alpha: float = ALPHA
) -> int:
    """Largest adverse count whose exact null lower-tail p-value <= alpha."""
    critical = -1
    for k in range(n + 1):
        if binomial_cdf(k, n, null_rate) <= alpha:
            critical = k
        else:
            break
    return critical


def minimum_n_for_power(
    adverse_rate: float,
    target_power: float,
    null_rate: float = NULL_ADVERSE_RATE,
    alpha: float = ALPHA,
) -> dict[str, float | int]:
    """Find the first n with the target exact one-sided test power."""
    for n in range(1, MAX_N + 1):
        critical = critical_max_adverse(n, null_rate, alpha)
        power = binomial_cdf(critical, n, adverse_rate)
        if power >= target_power:
            return {"n": n, "max_adverse": critical, "power": power}
    raise RuntimeError(f"No solution found through n={MAX_N}")


def minimum_retention_denominator(
    frontier_success_rate: float = 0.80,
    minimum_successes: int = 606,
    target_probability: float = 0.80 ** (1 / 5),
) -> dict[str, float | int]:
    """Find N so P[Bin(N, rate) >= minimum_successes] reaches target."""
    for n in range(minimum_successes, MAX_N + 1):
        probability = binomial_sf_at_least(minimum_successes, n, frontier_success_rate)
        if probability >= target_probability:
            return {"n": n, "probability": probability}
    raise RuntimeError(f"No solution found through n={MAX_N}")


def build_report_data() -> dict[str, object]:
    powers = []
    for target_power in TARGET_POWERS:
        for adverse_rate in ADVERSE_RATES:
            result = minimum_n_for_power(adverse_rate, target_power)
            powers.append(
                {
                    "target_power": target_power,
                    "adverse_rate": adverse_rate,
                    **result,
                }
            )
    return {
        "assumptions": {
            "null_adverse_rate": NULL_ADVERSE_RATE,
            "one_sided_alpha_per_endpoint": ALPHA,
            "target_joint_power_illustration": 0.80,
            "independent_endpoints_for_joint_power_illustration": 5,
            "iid_bernoulli": True,
        },
        "power_sensitivity": powers,
        "retention_denominator_illustration": {
            "frontier_only_success_rate": 0.80,
            "minimum_frontier_successes": 606,
            **minimum_retention_denominator(),
        },
        "warning": "Illustrative IID sensitivity, not a final product sample size.",
    }


if __name__ == "__main__":
    print(json.dumps(build_report_data(), indent=2, sort_keys=True))
