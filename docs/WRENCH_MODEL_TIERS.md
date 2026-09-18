# Wrench model tiers

Wrench currently has two verified text-only NVFP4 artifacts derived from the
official Qwen3.6-35B-A3B source. They are selectable local experiments, not
production releases.

| Tier | Parameters | Packed weights | Full artifact | Guarded 28-case result | Best use |
| --- | ---: | ---: | ---: | --- | --- |
| Compact 8E | 3,881,244,016 | 3.169 GiB | 3.188 GiB | 11/28 accepted, 19/28 expected outcomes, 0 prohibited | Lowest footprint and latency |
| Larger 16E | 4,888,532,336 | 3.697 GiB | 3.718 GiB | 14/28 accepted, 22/28 expected outcomes, 0 prohibited | More useful routine-task candidate |

Artifacts:

- Compact: `D:\models\Wrench-Qwen3.6-8expert-profiled-W4A16-NVFP4-calibrated-v7-Safety-ExplicitSchema-TextOnly-HF`
- Larger: `D:\models\Wrench-Qwen3.6-16expert-profiled-W4A16-NVFP4-calibrated-v3-ExplicitSchema-TextOnly-FTW`

Use either tier only through the strict local adapter and independent verifier.
Regex, destructive, traversal, malformed, unsupported, or uncertain requests
must abstain and preserve the original request for the stronger-model
fallback. Learned routing is explicitly `DISABLE` in
`config/wrench-routing-policy.json`.

The 16E tier is the current recommendation when usefulness matters more than
minimum latency. The 8E tier is the compact option when local footprint and
latency matter more. These comparisons are synthetic diagnostics. Authorized
real workflow traces, paired token savings, human approval, and production
enablement remain open.
