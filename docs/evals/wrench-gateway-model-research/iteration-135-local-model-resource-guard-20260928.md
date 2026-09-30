# Iteration 135: local model runtime resource guard

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-LOCAL-MODEL-RESOURCE-GUARD-ITER135`  
Status: **source guard implemented; focused unit checks passed**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Change

Updated [the local model runner](../../../examples/gateway_context_mvp/run_local_model_mvp.py) so it checks the 10% RAM and VRAM reserve before loading, starts resource sampling before model loading, and passes a Transformers stopping criterion that prevents continued token generation after a sampled floor breach or telemetry failure. The sampler latches a floor breach for the lifetime of the run. The receipt records both the breach and whether generation was aborted by the guard.

Synchronous model loading cannot be interrupted by a generation stopping criterion. Preflight admission remains required; if loading crosses a floor, the sampler prevents generation once loading returns. This is cooperative runtime protection, not an OS-level memory limit or kill switch. Updated the [demo README](../../../examples/gateway_context_mvp/README.md) with this limitation and the implemented behavior.

## Verification

```text
python -m unittest tests/test_local_model_resource_guard.py -v
Ran 3 tests in 0.004s
OK
```

The three focused tests cover latching a RAM/VRAM reserve breach, passing the stop callback to generation, and stopping on sampler telemetry error. They are unit checks for the guard, not model-quality tests.

`git diff --check` passed. Git emitted mixed-line-ending warnings for pre-existing dirty files.

## Identities and admission

| File | SHA-256 |
|---|---|
| `examples/gateway_context_mvp/run_local_model_mvp.py` | `5F564296CC6D653C68C18EB921DCC19AF025902CB7DE4F6E35D3E80CDB5E9CFF` |
| `examples/gateway_context_mvp/README.md` | `A2220D8F45880B696EFA2B8D7320478731A45126C8D3F2CEFF3F685FDF8D5154` |
| `tests/test_local_model_resource_guard.py` | `D3016CBFEBCF17ABADD124CB66E23CA18A15816983DFB1A438F928073B86EC1C` |

Reserved `25,000,000` bytes under the assignment ID before source and test artifacts. The reservation was retained through report creation and released after output accounting. The model-runtime exercise was admitted separately under Iteration 137. The gateway goal hash was preserved so the existing Fit-03 package review identity was not invalidated.

## Limits and next step

This change does not prove the generation backend will interrupt at an arbitrary point, bound synchronous model loading, or protect the host from unrelated memory consumers. Iteration 137 exercised this path during one local synthetic retrieval episode and stayed above the measured 10% resource floors. Broader runtime interruption and sustained engineering tests remain open. The product's 95/5 completion and routing, success retention, frontier-token and all-in-cost savings, and all-day engineering targets remain active and unproven.
