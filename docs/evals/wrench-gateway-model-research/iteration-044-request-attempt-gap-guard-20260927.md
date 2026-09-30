# Iteration 044: reject missing request attempt indices (2026-09-27)

## Change

The paired OpenCode request accountant now requires zero-based, contiguous
attempt indices within each episode arm. Captures may arrive out of order, but
gaps and duplicate attempt numbers are rejected before aggregation. This
closes a concrete path where a receipt set could include a retry gap while
still contributing an apparently valid byte total.

Regression cases were added for a missing index (`0, 2`) and duplicate index
(`0, 0`). The source and test files parsed successfully and have no trailing
whitespace. The focused unit tests were not run because free RAM was 9.95%,
below the runtime floor.

## Evidence boundary

This check improves the bounded accountant but does not prove complete capture.
The caller still supplies `capture_complete`, the accountant is not wired to
the live OpenCode transport, and an omitted trailing call can remain invisible
if the caller incorrectly closes an episode. Transport-level episode closure
and all-request visibility remain required before reporting real token savings.
No inference, model training, benchmark, paid SubRoute call, or provider spend
occurred.

## Resource and storage record

At admission, storage was `WITHIN_LIMIT` at 10,992,505,681 actual bytes plus
8,103,000 bytes in existing reservations, including the external SubRoute
checkout. This job reserved 300,000 bytes for bounded source, test, and report
changes. C: had 132.17 GiB free. The host sample was 3,253.9/32,701.8 MiB RAM
free (9.95%) and 15,210/16,311 MiB VRAM free. No Wrench process was running.

## Exact source identities

| File | SHA-256 |
| --- | --- |
| `src/wrench_harness/opencode_request_capture.py` | `5ADD10269DE39CB615656093ED13CDF4B61098736F89E6E6D76D189B9629928F` |
| `tests/test_opencode_request_capture.py` | `D4B4BD22941AE21E8C82E48A34F38ED361640F902B6786392740A5E37173C0EC` |

## Next step

When RAM and VRAM clear the runtime floor, run the focused accountant suite.
Then close the larger evidence gap by integrating transport observation with a
trusted task-harness episode-close event. Keep product token savings unavailable
until actual provider usage and task outcomes are paired on the frozen workload.
