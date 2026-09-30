# Iteration 138: resource-stop coverage for local model runners

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-GATEWAY-INFERENCE-STOP-GUARD-ITER138`  
Status: **three additional local inference entry points now stop generation on resource breach; focused checks passed**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Finding and change

A source audit found that the single-case runner already passed the resource sampler to a Transformers stopping criterion, but three related local inference scripts did not. They sampled RAM and VRAM, yet could continue token generation after a threshold breach until the current model call ended.

Updated the three entry points to share the existing bounded criterion from `run_local_model_mvp.py`:

- [Three-case local matrix](../../../examples/gateway_context_mvp/run_local_model_matrix.py)
- [Adaptive context-budget sweep](../../../examples/gateway_context_mvp/run_local_model_budget_sweep.py)
- [Paired full-context versus E0 baseline](../../../examples/gateway_context_mvp/run_paired_local_context_baseline.py)

Each generation now checks the live sampler and stops at a generation step after telemetry failure or a sampled RAM/VRAM floor breach. If a breach occurs, the scripts record an incomplete/aborted case and stop the remaining cases or sweep. Model-load exceptions and preflight failures also stop and join the sampler thread. Synchronous model loading itself remains non-interruptible; its preflight admission remains necessary.

## Verification

```text
python -m unittest tests/test_local_model_resource_guard.py -v
Ran 4 tests in 0.072s
OK
```

The fourth test parses each of the three runner sources and verifies that every `generate` call receives `stopping_criteria` from the shared guard helper. The other tests exercise threshold latching, live callback behavior, and fail-closed telemetry handling. `git diff --check` passed; Git printed existing mixed-line-ending warnings for unrelated dirty files.

No local-model inference or provider request ran in this iteration. The source-level wiring check does not prove interruption behavior for each runner under a live CUDA memory-pressure event. Iteration 137 exercised the same guard helper in the single-case runner, but these three wrappers still need a safely admitted runtime confirmation.

## Exact identities

| File | SHA-256 |
|---|---|
| `examples/gateway_context_mvp/run_local_model_matrix.py` | `F3ECEFD88F1C91A81BDF1BE0723FF9D97CFD93373C11890192840121083725D2` |
| `examples/gateway_context_mvp/run_local_model_budget_sweep.py` | `3F7875004F017690753CAEC2AF6119C03D1A1E5E2986C1A819C2B823821E5005` |
| `examples/gateway_context_mvp/run_paired_local_context_baseline.py` | `C2A89358838D7FADBACAD1D0DD9535C584430AB723CD72D17EB761320DB689DF` |
| `tests/test_local_model_resource_guard.py` | `EFEC74A41E2B8BEEC3A9E0732155E2FEF31BA4ED64A77F5E36B1D3C95C4B89C1` |

The gateway goal hash remained unchanged, preserving the existing hash-bound Fit-03 package review identity.

## Admission and limits

Reserved `25,000,000` bytes under this assignment before code/test artifacts. The pre-report checker returned `WITHIN_LIMIT` with the repository, approved data root, SubRoute, worker checkout, hourly automation, and Docker WSL model volume included. Actual use was 15,436,344,585 bytes; active reservations including this job were 31,103,000 bytes, for 15,467,447,585 projected bytes against the strict 50 GB ceiling. RAM was about 19.83% free and VRAM was 15,212 / 16,311 MiB free at the initial source-audit sample. No inference was admitted because this iteration only required source changes and unit checks.

This iteration improves resource-safety coverage. It does not change measured token savings or establish LoRA utility, completion quality, 95/5 routing, frontier-token reduction, all-in cost, or all-day engineering. The product targets remain active and unproven.
