# Iteration 104: stable-source E0 focused runtime verification

Date: 2026-09-28  
Assignment: `WRENCH-GW-STABLE-EVIDENCE-097-PYTEST-DEP-AND-VERIFY-105-20260928`  
Status: **19 focused tests passed; stable-source mechanics verified on the current source snapshot; token utility and product outcomes remain unmeasured**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree remains dirty)  
Gateway goal SHA-256: `817E1918334F19A42DDDDCE857436380CC2ABFFB8B361BA19DDFECAFD4968146`

## Result

After updating the project-local Python 3.11 environment with pytest, ran the
two focused suites identified by Iteration 097:

```text
python -m pytest -q tests/test_execution_state_store.py tests/test_execution_state_e0_context.py
19 passed in 3.39s
```

The tests exercise the current execution-state store and E0 revalidation path,
including replay, evidence identity, stale or changed sources, and prompt
preparation boundaries covered by those suites. The earlier attempt with the
system Python 3.13 failed before collection because pytest was absent. The
repository `.venv` is Python 3.11.16 and also initially lacked pytest. Pytest
9.1.1 and its five dependencies were installed into that ignored project
environment with `uv pip`; no repository dependency manifest was changed.

This is focused mechanics verification, not coding-task utility. No paired
coding episodes or tokenizer comparisons ran, and no frontier call was made.
The 95/5 completion/routing, 95% retained success, frontier-token savings,
all-in cost savings, LoRA value, and sustained all-day engineering claims
remain unproven.

## Tested identities

| File | SHA-256 |
|---|---|
| `src/wrench_harness/execution_state.py` | `C0B6F0A73AA936AD53025E0F506F619197506C40EE4507F98EBEAAF5E9AC3515` |
| `src/wrench_harness/execution_state_store.py` | `7518936888BE0B300B1CC3102B902339BD15632AC66B2B56DABE9727C7DD7117` |
| `src/wrench_harness/e0_context_pipeline.py` | `F28378DD6712738506918D23FD34E121E4EFE9C05A0F5020267EB3A38FE74251` |
| `tests/test_execution_state_store.py` | `51BB14AF0BBFAF94531E6FF591B49F544DFAC4EACC68BEFC244ADD2766BB9EB3` |
| `tests/test_execution_state_e0_context.py` | `B12FC2E9CFD9D79051D09A9777CCFB468F3123B704175D365DBC4565F575E534` |

## Admission and limits

The test job reserved 200,000,000 bytes as
`WRENCH-GW-STABLE-EVIDENCE-097-PYTEST-DEP-AND-VERIFY-105-20260928`. The
storage checker included the Docker Desktop WSL model volume and external
Wrench repositories; it reported `WITHIN_LIMIT` at 15,428,927,595 actual
bytes, 206,603,000 reserved bytes, and 15,635,530,595 projected bytes against
the 50,000,000,000-byte ceiling. C: had 143,792,930,816 bytes free.

Resource samples: before dependency install/test, 27.64% system RAM free and
15,217 MiB of 16,311 MiB VRAM free; immediately before tests, 27.14% RAM and
15,229 MiB VRAM free; after, 27.78% RAM and 15,217 MiB VRAM free. All sampled
values cleared the 10% runtime floor. The test process was short; this is not
continuous telemetry for a long-running workload.

The prior `WRENCH-GW-STABLE-EVIDENCE-097-20260928` reservation covered the
pending verification and is now complete. Iteration 097's remaining next
steps are paired source-only, transcript, and stateful-context measurements
on frozen coding episodes with target-tokenizer counts, correctness outcomes,
recovery/retry accounting, and all-in cost. Model fitting remains gated by a
fresh exact package review, and the held-out split remains sealed.
