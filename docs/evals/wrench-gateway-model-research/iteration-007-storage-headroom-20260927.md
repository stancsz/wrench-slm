# Iteration 007: additive storage headroom gate

Date: 2026-09-27 (America/Edmonton)

Status: **ADDITIVE SPACE FIX IMPLEMENTED; EXACT-HASH REVIEW PENDING; NO PREFLIGHT OR FIT RUN**

## Review 03 result and response

Independent assignment `WRENCH-GW-ATTN-FIT-PATH-REVIEW-20260927-03`
(`2a4a8fbb-9c3d-4f1b-bb71-5322d40a1974`) verified all seven assigned hashes
before and after review. It returned **FAIL** on a conditional P2 storage
headroom gap. The trainer separately checked free space against the job's peak
reservation and against the 5 GiB operating reserve. That enforced the larger
threshold, but the storage policy requires their sum, so actual writes could
consume the operating reserve.

The runner now computes the minimum destination free bytes as
`active_reservation_bytes + 5 GiB`. It enforces this before claiming a job and
again through the reservation checkpoint function. This applies to both the
250,000,000-byte preflight 05 reservation and the 1,500,000,000-byte fit 03
reservation. The focused tests assert both arithmetic cases and reject a
negative reservation value. This source/protocol/goal revision has a new
identity and needs exact-hash review 04 before any model/data job.

## Current candidate and run admission

The candidate remains the pinned local Qwen3.5-0.8B with only the
`softmax-attention-only` profile: 24 `self_attn` q/k/v/o modules and 540,672
trainable parameters. Fit 03 has a 96-step hard maximum and writes an
unactivated candidate. The fit still requires at least 25% free RAM at start
and at least 10% free RAM/VRAM throughout. Preflight 05 requires at least 10%
free RAM/VRAM throughout. For either job, free C: space must remain at least
the active job reservation plus 5 GiB at admission and each checkpoint.

Job IDs remain unique:

- Preflight 05: `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-05-ATTN`
- Fit 03: `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN`

The heldout scorer is still pinned to fit 02 and needs a separate candidate-
specific update and review before any heldout read.

## Live resource and storage snapshot

| Resource | Observation | Gate result |
|---|---:|---|
| RAM free | 17.58% | Below fit's 25% start gate; no fit |
| GPU | NVIDIA GeForce RTX 5060 Ti, 16,311 MiB total, 15,244 MiB free; UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021` | Above 10% at sample time; recheck before jobs |
| C: free | 156,135,538,688 bytes | Above reservation plus 5 GiB at sample time; recheck before every job |
| Wrench storage | 10,955,437,406 bytes actual; 11,103,000 bytes active reservations; 39,033,459,593 bytes reported headroom | Within 50 GB; implementation reservation remains active |

These readings are not future admission. Run storage status and reserve a new
unique job before each artifact-producing job. The 25% fit start gate remains
separate from the 10% runtime floors; attention-only LoRA does not reduce the
FP32 foundation footprint.

## Checks completed

- `python -m unittest tests.test_gateway_lora_profiles -v`: 12 tests passed,
  including no-replace rename behavior, resource minima, and reservation plus
  5 GiB arithmetic.
- `python -m py_compile tools/train_gateway_lora_screen_02_gpu.py tests/test_gateway_lora_profiles.py`: passed.
- `git diff --check`: passed. Git emitted line-ending warnings for unrelated
  existing working-tree files only.
- The default Python interpreter does not have pytest; the focused stdlib
  `unittest` suite passed.
- No model/data/heldout file was read. No SubRoute generation, provider spend,
  training, or inference occurred.

## Exact hashes awaiting review 04

Expected repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`.

| File | SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_02_gpu.py` | `62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC` |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `tests/test_gateway_lora_profiles.py` | `84D1C4B4EDE45C0880E1F2469CC9A165D8C62B8DFB163A58D024A4B42C6DA614` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `5D5AC50CD1A68B66AE964AC54B387B052F276BC2C534EDF60EA429F8C109B87A` |

Review 04 must include this record and
`docs/northstar/STORAGE_AND_RECOVERY.md` at SHA-256
`FBD7BFD399B97C2697C5AB77154E49E61F41FF007B1EB8908B34B18927886B26`. Any
change after review invalidates the relevant hash.

## Next gates

1. Obtain exact-hash PASS for this additive-space revision before any
   preflight or fit.
2. Recheck storage/reservations, RAM/VRAM, processes, pinned runtime and C:
   free space. If admitted, run only preflight 05; keep its reservation until
   stopped and fully accounted.
3. Keep fit 03 blocked until preflight matches the current candidate hashes,
   its reservation is released, and live 25% RAM-start, 10% RAM/VRAM, storage,
   and reservation-plus-5-GiB checks all pass.
4. Update and independently review the scorer before any heldout access.
5. Keep SubRoute generation closed until an aggregate USD cap and a hard
   caller-side guard against missing/mismatched per-call usage and cost
   receipts are in place.

Even successful source review or preflight demonstrates compatibility only.
No Wrench policy quality, task value, coding ability, all-day operation,
95%-local completion, 5% escalation, 95% token savings, or 95% lower all-in
cost has been proven.
