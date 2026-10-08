# Wrench goal

The single active objective is to reduce frontier input plus output tokens by
at least 30% on comparable complex coding tasks with completion quality
preserved. Local Qwen tokens have zero weight. Frontier spend is capped at $1
per stable task across all attempts, retries, verification, diagnostics and
reruns.

[`docs/goal/wrench-token30/GOAL.md`](docs/goal/wrench-token30/GOAL.md) is the
authoritative acceptance contract and contains the one current checkpoint.
[`docs/archive/2026-10-08-clean-slate/LEARNINGS.md`](docs/archive/2026-10-08-clean-slate/LEARNINGS.md)
records prior findings. The storage and recovery boundary is in
[`docs/operations/STORAGE_AND_RECOVERY.md`](docs/operations/STORAGE_AND_RECOVERY.md).

No historical goal, report, design note or experiment can create a competing
work queue. Resume supporting work only when the active checkpoint names it as
a necessary dependency. The target remains unproven until a matched,
quality-passing comparison meets the 30% threshold.
