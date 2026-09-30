# Iteration 055: verify the live SubRoute at port 4000 (2026-09-28)

## Live route check

The owner directed the experiment to use the existing SubRoute at
`http://127.0.0.1:4000`. Fresh read-only GET requests returned HTTP 200 for:

- `/health/liveliness`, returning `I'm alive!`
- `/api/active-model`, reporting `active_model: openrouter`, `mode: force`,
  and `policy_version: 4`
- `/v1/models`, returning 19 model entries, including the `openrouter` alias

The local gateway is reachable and its active configuration forces the alias
through its remote OpenRouter route. This confirms which local gateway to use
for the experiment. It does not prove teacher-generation behavior, token
accounting, LoRA effectiveness, or any savings. A GET to `/health` timed out;
the correct live check is `/health/liveliness`.

No POST, generation, credential access, provider traffic, or spend occurred.
The numeric campaign USD cap is still absent, so the shared caller's approval
and worst-case reservation gates remain closed. Use this SubRoute for a future
approved comparison, and verify the exact model and billed-cost receipt through
the guarded capture caller.

## Current limits and next step

The current free-RAM sample was 3,348.4 / 32,701.8 MiB (about 10.24%), close
to the 10% runtime floor. No test suite, model runtime, inference, training,
benchmark, package build, or delegated job ran. First wait for comfortable
resource margin, then run the hash-bound SubRoute caller checks and verify the
provider-control metadata path without upstream transport. A paid generation
comparison still requires a numeric campaign cap.

The staged sub-10B LoRA, verified 95/5 local/frontier task mix, 95% frontier
token reduction, 95% lower all-in cost, and sustained all-day engineering
remain unproven. See the [active goal](../../goal/wrench-gateway-model-research/GOAL.md)
and [Iteration 054](iteration-054-cache-stable-tool-pruning-20260928.md).
