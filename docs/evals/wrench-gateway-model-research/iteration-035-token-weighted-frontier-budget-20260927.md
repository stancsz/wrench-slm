# Iteration 035: token-weighted frontier budget (2026-09-27)

## Question

Does routing at most 5% of task episodes to a frontier model establish at least
95% frontier-token savings? No. The two thresholds have different denominators.

## Result

For paired planned episodes `i`, let `b_i` be all provider-reported frontier
tokens in the frontier-only arm and `h_i` all provider-reported frontier
tokens in the hybrid arm, including retries, verification, fallback,
compaction, re-fetch, cache-miss billing, and auxiliary calls. The token gate is

`sum(h_i) <= 0.05 * sum(b_i)`.

The episode escalation gate remains a separate condition:

`count(episodes with any frontier call) / count(all planned episodes) <= 0.05`.

If exactly 5% of episodes are routed and each routed episode consumes its
frontier-only token volume, the token ratio is exactly 5% only when the routed
episodes represent 5% of the baseline's total token volume. This leaves no
margin for retries or other remote work. If the routed 5% account for 12% of
baseline tokens, sending their full baseline contexts uses 12% of baseline
tokens and saves only 88%. To pass 95% savings, all hybrid calls on that routed
set would have to consume at most `0.05 / 0.12 = 41.7%` of that set's
frontier-only tokens, even if all non-routed episodes use zero frontier
tokens.

## Protocol change

Updated the product proof design to require both estimands and a route-set
token-mass diagnostic. Per-pair provider receipts must support an auditable
ratio of sums; do not average per-episode savings percentages or infer token
savings from route counts. Preserve all planned episodes and failures.

This is an algebraic feasibility check, not an observed Wrench result. No model
inference, provider request, spend, or test was run. Live RAM remained below
the 10% job floor during this iteration, so model and caller runtime evidence
is still pending.

## Next evidence

On an authorized paired workload, report the baseline token mass represented by
the routed set, the hybrid frontier-token sum, and the separate episode route
rate with confidence bounds. Then determine whether any route policy can meet
both bounds while preserving verified task success and all-in cost. Do not
authorize paid SubRoute capture without the numeric aggregate cap and verified
caller receipt controls.
