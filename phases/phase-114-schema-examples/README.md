# Phase 114: generic schema few-shot probe

## Result

Five generic assistant examples were temporarily inserted into the model
fallback prompt and the same NVFP4 checkpoint was evaluated over all 220
historical cases.

Receipt: `../phase-114-full-220-schema-examples/full-220-schema-examples.json`.

| Arm | Correct outcomes | Exact eligible accepts | Prohibited accepts | Median | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| v7 pure baseline | 51/220 | 3/120 | 6 | 344.246 ms | 878.825 ms |
| generic schema examples | 63/220 | 8/120 | 14 | 329.450 ms | 819.850 ms |

The examples improve formatting slightly but make safety materially worse.
They are rejected and are not part of the current source path or public
package. The source was reverted to the pre-probe behavior after the receipt
was captured.
