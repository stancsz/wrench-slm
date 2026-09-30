# Iteration 005: attention-only fit path preparation

Date: 2026-09-27 (America/Edmonton)

Status: **CODE AND PROTOCOL PREPARED; EXACT-HASH REVIEW PENDING; NO PREFLIGHT OR FIT RUN**

## User direction and boundaries

The user reconfirmed SubRoute at `http://127.0.0.1:4000` and authorized trying
any model below 10B when its actual hardware path runs smoothly. The existing
Wrench data contract admits only the already-pinned Qwen3.5-0.8B candidate and
synthetic train/dev rows for this next local LoRA stage. This iteration does
not select or download another model, call the gateway, open heldout, or
activate an adapter. The numeric aggregate USD cap is still absent, so paid
generation remains closed.

## Candidate path prepared

The new path isolates attention-only fit 03 from the historical all-projection
fit 02 and preflight 04. The active CLI requires an explicit `--preflight-only`
or `--fit` mode and accepts only `softmax-attention-only`. The instantiated
candidate must match 24 `self_attn` q/k/v/o modules and 540,672 trainable
parameters. A fit receipt must consume a fresh matching preflight 05 receipt
whose model, data, protocol, runner, runtime, device, adapter profile, target
count, parameter count, one-step outcome, resource log and released
reservation all match.

The new identities are:

| Job | ID | Path |
|---|---|---|
| Preflight 05 | `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-05-ATTN` | `C:\\wrench-slm-data\\logs\\wrench-gateway-model-research\\lora-screen-02-preflight-05-attention-only` |
| Fit 03 | `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN` | `C:\\wrench-slm-data\\artifacts\\wrench-gateway-model-research\\lora-screen-02\\fit-03-attention-only` |

Fit 03 is bounded to exactly 96 optimizer steps, at least 1,500,000,000 bytes
of storage reservation, 512 MiB sampled scratch, a 100 MiB adapter, at most
20 MiB per log, at least 5 GiB free on C:, and a 25% free-RAM start buffer.
At least 10% RAM and VRAM must remain free throughout. The new adapter path is
a candidate path only. A pinned Windows tree inventory verifies every
single-link adapter file before and after the atomic staging move; hash or
inventory mismatch prevents a success receipt. No base, Core, or active
adapter is changed.

The existing heldout scorer remains pinned to fit 02 paths. Before any heldout
access, it needs a separate candidate-specific update for fit 03, exact-hash
review, storage admission and its development-only inference preflight.

## Live admission sample

| Resource | Observation | Decision |
|---|---:|---|
| RAM free | 17.86% | Below fit start requirement of 25%; no full fit |
| GPU | NVIDIA GeForce RTX 5060 Ti, 16,311 MiB total, 15,252 MiB free; UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021` | Above 10% idle reserve at sample time; recheck before each job |
| C: free | About 156 GB | Above 5 GiB minimum at sample time; recheck before each job |
| Wrench aggregate storage | 10,955,411,676 bytes actual plus 11,103,000 bytes in active reservations; 39,033,485,323 bytes projected headroom | Within 50 GB; implementation reservation remains until this iteration is accounted |

The resource sample is not a guarantee for the next process. Preflight 05
requires its own fresh 250,000,000-byte reservation and live 10% RAM/VRAM
admission. Fit 03 must separately pass the 25% RAM start check and receive a
fresh 1,500,000,000-byte reservation after the stopped preflight reservation
is accounted for and released.

## Checks completed

- `python -m unittest tests.test_gateway_lora_profiles -v`: 8 tests passed,
  including the new active-profile, mode, and fit-route checks.
- `python -m py_compile tools/train_gateway_lora_screen_02_gpu.py tests/test_gateway_lora_profiles.py`: passed.
- `git diff --check`: passed; Git printed only existing line-ending warnings
  for unrelated working-tree files.
- `python -m pytest ...` could not run because pytest is not installed in the
  default Python 3.13 interpreter. The focused stdlib unittest suite ran
  successfully instead.
- SubRoute liveness/model reads remain the prior read-only evidence in
  [iteration 004](iteration-004-subroute-readonly-20260927.md). No generation
  call or spend occurred.

## Exact source identities awaiting review

Expected repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`.

| File | SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_02_gpu.py` | `3197498CD6A5589CCB0AD6C81B6DB19216D53421F7F5BF68A6ED7D92A594AFB8` |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `tests/test_gateway_lora_profiles.py` | `60D44DECC9D4FDBABFCBEFD6DF4DCB922302822D7C5B0FEEC5A15F6822E00EB0` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `5C7B41926DE1387582137EFA988E75A3C3D766491461359EDD9A83AA2F596741` |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `193A5F5E0181E23B30AE24421C190B5D70F49406BFABF68B76AE415D9547835C` |

This record, the five listed source artifacts, the pinned-tree helper, and the
current storage policy are the read-only review scope. Any source or protocol
change after review invalidates the corresponding reviewed hash. No model,
dataset, environment, adapter or heldout file was read in these checks; only
the previously recorded hardware/storage status was sampled.

## Next gates

1. Independent exact-hash static review must return PASS with no P1/P2
   blocker. No model/data job runs before that disposition.
2. Recheck storage, RAM, VRAM, C: free space, processes, runtime identities,
   and the actual active reservation. If admitted, run only one-step preflight
   05 and account/release its reservation after the process stops.
3. Keep fit 03 blocked unless preflight 05 matches all candidate hashes,
   minimums and profile checks, plus fresh >=25% free RAM, >=10% ongoing
   RAM/VRAM, destination-space and storage gates.
4. After a fit result, update and review the heldout scorer under a new
   candidate-specific protocol before opening heldout once.
5. Do not call the local SubRoute for a generation comparison until the user
   supplies a numeric aggregate USD cap and the request caller enforces it
   against provider/model/usage/cost receipts.

Passing the source review, preflight, or fit is only compatibility/training
evidence. None proves model quality, coding ability, 95% task value, 5% frontier
escalation, 95% token or dollar savings, or full-day engineering.
