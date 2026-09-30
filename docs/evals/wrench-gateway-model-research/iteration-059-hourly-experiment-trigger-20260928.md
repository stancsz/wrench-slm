# Iteration 059: make the hourly job launch the experiment when admitted

## Hourly automation

The existing `wrench-hourly-token-reduction-monitor` heartbeat was already
ACTIVE, hourly, and attached to this thread. Updated that job instead of
creating a duplicate. Its prompt now treats the owner's instruction as
authorization to start the bounded local LoRA experiment as soon as the
current protocol gates pass. It keeps the under-10B model choice open, starts
with the already inventoried Qwen3.5-0.8B controller, and says not to let the
unrelated SubRoute spend cap block provider-free training. It preserves the
10% operating floor, the fit-03 25% RAM start gate, storage admission, exact
hash/data/runtime checks, stop conditions, and the rule that candidate weights
stay inactive until evaluation and rollback pass.

The automation remains ACTIVE and hourly after the update. It directs hourly
re-measurement and launch once RAM is at least 25% at process start, RAM/VRAM
can remain at least 10% free, and the remaining exact run gates pass. Between
10% and the 25% training gate it keeps training and model runtime closed.

## Current host admission

Read-only host inspection found:

- System RAM: 3,283.4 / 32,701.8 MiB free (10.04%). This is only 13.4 MiB
  above the 10% floor and below the experiment's 25% start gate.
- NVIDIA GeForce RTX 5060 Ti: 15,235 / 16,311 MiB VRAM free.
- C: free space: 141.04 GB.
- No Wrench training, inference, or benchmark process was present in the
  process query.

The pinned Qwen3.5-0.8B remains the staged first controller candidate. Its
GPU-fit protocol requires at least 25% free system RAM before fit-03 starts,
and at least 10% free RAM and VRAM throughout the job. Thus the machine is not
admitted now even though the GPU has ample free memory. No tests, runtime,
inference, training, benchmark, packaging, or delegation ran. No provider POST,
credential read, or spend occurred.

The SubRoute at `http://127.0.0.1:4000` remains forced to remote alias
`openrouter`. The route is available for a later frontier comparison, but the
numeric campaign USD cap is still absent. The hourly prompt does not ask again
and prohibits paid generation until the shared budget ledger and cap exist.

Storage admission was `WITHIN_LIMIT`. Before this log reservation, actual use
was 10,993,211,091 bytes with 8,103,000 bytes in active reservations. This
documentation job reserved 80,000 bytes under
`WRENCH-HOURLY-GATE-AND-HARDWARE-20260928-01`; release it after final accounting.

No Luna advisor call was warranted: the current decision follows explicit
repository gates, and further consultation would not change the next action.
No subagent was started because this is one sequential automation update and
hardware is at the resource floor; parallel work would not materially improve
the result.

## Next action and evidence status

At the next hourly check, remeasure fresh RAM/VRAM and process state. When the
25% fit-start threshold and all exact admission gates pass, run the bounded
protocolized LoRA experiment without waiting for another user confirmation.
Do not lower or replace the 95/5 task-success, 95% frontier-token reduction,
95% all-in cost reduction, or all-day engineering criteria. Those outcomes
remain unproven.
