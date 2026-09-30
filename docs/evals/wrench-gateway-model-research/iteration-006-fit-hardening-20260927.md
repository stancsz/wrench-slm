# Iteration 006: fit-path hardening after review

Date: 2026-09-27 (America/Edmonton)

Status: **FIT HARDENING IMPLEMENTED; NEW EXACT-HASH REVIEW PENDING; NO PREFLIGHT OR FIT RUN**

## Review result and response

Independent assignment `WRENCH-GW-ATTN-FIT-PATH-REVIEW-20260927-02`
(`b4c7d936-22b8-48e3-9c23-1f0e07b4e2a9`) verified every assigned hash and
returned **PASS for the preflight-05-only path**, subject to fresh live
admission checks. It did not authorize preflight or fit. It found a
conditional P2: `Path.replace` could overwrite an output directory created
after the precheck. It also recommended recording resource minima and making
the 5 GiB physical-space gate apply to preflight as well as fit. Its source
scope did not include the heldout scorer.

The latest source replaces `Path.replace` with a Windows `os.rename` no-replace
operation, keeps the post-move hash-inventory equality check, and adds a focused
preservation test for an existing candidate directory. Both preflight and fit
now fail before claiming a job if destination free space is under 5 GiB. The
preflight verifier checks that manifest RAM/VRAM minima equal minima recomputed
from the hash-bound resource log; finalization records both minima in every
receipt. Earlier fit instructions in the protocol are explicitly marked
historical and superseded. These changes require a new review; assignment 02
does not cover them.

## Current candidate and run admission

Candidate remains the pinned local Qwen3.5-0.8B with only the
`softmax-attention-only` profile (24 `self_attn` q/k/v/o modules, 540,672
trainable parameters). This is a narrow Wrench context/routing policy
candidate, not an open-ended coding agent. The hardcoded 96-step maximum is
retained. Fit 03 needs a new 1,500,000,000-byte reservation, at least 25% free
RAM at process start, at least 10% free RAM and VRAM throughout, and at least
5 GiB destination free space. Preflight 05 needs a new 250,000,000-byte
reservation, the 10% RAM/VRAM floors, and the same 5 GiB free-space gate.

Job IDs remain unique:

- Preflight 05: `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-PREFLIGHT-20260927-05-ATTN`
- Fit 03: `WRENCH-GATEWAY-LORA-SCREEN-02-GPU-FIT-20260927-03-ATTN`

No output is activated. The heldout scorer still names fit 02 and must be
updated and independently reviewed under its own candidate-bound protocol
before any heldout access.

## Live resource and storage snapshot

| Resource | Observation | Gate result |
|---|---:|---|
| RAM free | 17.43% | Below fit's 25% start gate; no fit |
| GPU | NVIDIA GeForce RTX 5060 Ti, 16,311 MiB total, 15,249 MiB free; UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021` | Above 10% at sample time; recheck before jobs |
| C: free | 156,171,984,896 bytes | Above 5 GiB at sample time; recheck immediately before every job |
| Wrench storage | 10,955,427,999 bytes actual; 11,353,000 bytes active reservations; 39,033,219,000 bytes reported headroom | Within 50 GB; the implementation reservation is still active |

These snapshots are not future run admission. Preflight 05 and fit 03 each
need fresh status/reservation checks. The 25% free-RAM fit gate cannot be
waived because the candidate uses fewer LoRA weights; it does not reduce the
FP32 foundation or prove peak fit memory.

## Checks completed

- `python -m unittest tests.test_gateway_lora_profiles -v`: 11 tests passed,
  including active profile/mode checks, both no-replace rename paths, and the
  resource-minima summary.
- `python -m py_compile tools/train_gateway_lora_screen_02_gpu.py tests/test_gateway_lora_profiles.py`: passed.
- `git diff --check`: passed. Git printed line-ending warnings for unrelated
  existing working-tree files only.
- The default Python environment does not have pytest; the focused stdlib
  `unittest` command above passed.
- No model or dataset file was read; no SubRoute generation, provider spend,
  training, inference, or heldout access occurred.

## Exact identities awaiting assignment 03 review

Expected repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`.

| File | SHA-256 |
|---|---|
| `tools/train_gateway_lora_screen_02_gpu.py` | `543BA2A189A7B113CB16489AE17DC2B53098C43E5CCF0FC19D102967938C5BC3` |
| `tools/wrench_windows_pinned_tree.py` | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| `tests/test_gateway_lora_profiles.py` | `F13E62C474925423A35ECD81BC033D73EB8CF20EE76ECF111332462294F1FB2E` |
| `docs/evals/wrench-gateway-model-research/lora-screen-02-gpu-protocol-20260927.md` | `F45451F146ED5B136486EEB773124C3C99A8216CC8DB67F50094EEC6598BF111` |
| `docs/goal/wrench-gateway-model-research/GOAL.md` | `702ADE4EA8A27574271BF61592922FD21602B8A0F858F32EF91085AE347C71FF` |

Also inspect this iteration record and the pinned storage policy. Assignment 03
must verify every assigned hash before and after its read-only review. Any
source or protocol change invalidates the affected reviewed identity.

## Next gates

1. Obtain fresh exact-hash PASS for the fit-hardening revision before any
   model/data job.
2. Recheck storage, all reservations, host processes, live RAM/VRAM, C: free
   space, pinned runtime and input identities. If admitted, run only preflight
   05 and preserve/release its reservation after the job stops and files are
   accounted.
3. Keep fit 03 blocked until the matching preflight passes, its reservation is
   released, and fresh 25% RAM, 10% RAM/VRAM, 5 GiB disk, and storage gates
   pass.
4. Before heldout, build and review a scorer for fit 03. Keep the sealed data
   unopened until that scorer's one-shot admission completes.
5. Use SubRoute only for read-only inspection until the user supplies a
   numeric aggregate USD cap. The caller must have a hard cap and verified
   per-call provider/model/usage/billed-cost receipts before any generation
   run.

Compatibility and training success would still be distinct from verified
decision quality, coding ability, 95% local completion, at most 5% frontier
escalation, 95% frontier-token savings, 95% lower all-in cost, and all-day
engineering.
