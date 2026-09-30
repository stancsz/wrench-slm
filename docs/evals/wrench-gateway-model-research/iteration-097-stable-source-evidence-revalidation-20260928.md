# Iteration 097: stable-source evidence revalidation in E0

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-GW-STABLE-EVIDENCE-097-20260928`  
Status: **source implementation present and statically reviewed; focused runtime verification is pending the host RAM gate**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway research goal SHA-256: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Purpose

Iteration 096 bound persisted task facts to a complete source-snapshot identity.
That made a fact unusable after an unrelated repository edit, even when its
cited file was unchanged. This iteration carries the state-source
reacquisition work forward with a stable, namespaced path-plus-content
identity. A state fact is still unusable until E0 reads its cited file from
the current repository and checks the exact content hash.

## Implementation reviewed

- [`execution_state.py`](../../../src/wrench_harness/execution_state.py) gives source evidence an identity derived from the
  repository namespace, normalized source path, and content hash. The state
  event retains that source metadata in the hash-linked event chain.
- [`ExecutionStateStore.load_for_revalidation()`](../../../src/wrench_harness/execution_state_store.py) replays and checks the stored
  event chain without claiming that its source evidence is current. Its receipt
  explicitly marks current evidence as unverified.
- [`prepare_e0_context()`](../../../src/wrench_harness/e0_context_pipeline.py) accepts that receipt only after validating its exact
  type and bounded fields. It resolves every cited source path, checks the
  repository namespace, reacquires all cited paths against the current source
  tree, and compares current content hashes. If a source changed, is missing,
  or belongs to a different repository root, E0 returns without a prompt.
- After successful revalidation, state summaries cite the evidence IDs for the
  current snapshot, remain marked as untrusted prompt data, and enter normal
  context-budget selection. The result exposes whether execution-state
  evidence was verified for a ready prompt; the aggregate receipt records that
  source references were revalidated.
- Legacy evidence without stable source metadata is accepted only when it can
  be resolved against the exact original snapshot.

The source review confirms these guards and control-flow relationships by
inspection. It does not establish that the changed implementation passes its
focused tests or that state summaries reduce model tokens in a real coding
request.

## Current identities

| File | SHA-256 |
|---|---|
| [`execution_state.py`](../../../src/wrench_harness/execution_state.py) | `C0B6F0A73AA936AD53025E0F506F619197506C40EE4507F98EBEAAF5E9AC3515` |
| [`execution_state_store.py`](../../../src/wrench_harness/execution_state_store.py) | `7518936888BE0B300B1CC3102B902339BD15632AC66B2B56DABE9727C7DD7117` |
| [`e0_context_pipeline.py`](../../../src/wrench_harness/e0_context_pipeline.py) | `A4978FB700534982C0D2EED5FB621ADC925690574135555FE3A4518F5A76E8B6` |
| [`test_execution_state_store.py`](../../../tests/test_execution_state_store.py) | `51BB14AF0BBFAF94531E6FF591B49F544DFAC4EACC68BEFC244ADD2766BB9EB3` |
| [`test_execution_state_e0_context.py`](../../../tests/test_execution_state_e0_context.py) | `B12FC2E9CFD9D79051D09A9777CCFB468F3123B704175D365DBC4565F575E534` |

## Verification state

The focused suites are [`test_execution_state_store`](../../../tests/test_execution_state_store.py) and
[`test_execution_state_e0_context`](../../../tests/test_execution_state_e0_context.py). The added cases cover replay with
unverified evidence, stable source identity across an unrelated snapshot
change, rejection after cited-source edits or repository-root changes,
stateless compatibility, and the result's prompt-evidence verification
marker. **These current cases were not run in this iteration.** Iteration 095
and 096 test results predate the stable-ID/reacquisition changes and do not
count as verification of this source revision.

At 2026-09-28 10:06:36 UTC, system RAM was 2,681,135,104 / 34,290,302,976
bytes free (7.82%). The RTX 5060 Ti had 14,481 / 16,311 MiB of VRAM free.
A follow-up sample at 10:13:37 UTC was lower at 2,449,608,704 bytes free
(7.14%); VRAM was 14,559 / 16,311 MiB free. RAM stayed below the 10% runtime
floor, so no tests, inference, training, benchmark, package, or delegated job
ran. The focused tests remain the next verification action after a fresh
sample meets both runtime reserves.

Read-only GETs to the configured SubRoute at `127.0.0.1:4000` returned HTTP
200 for `/health/liveliness`, `/models` (19 aliases), and `/api/active-model`.
The active route remains `openrouter`, forced mode, policy version 4. No
completion or provider request was sent, no credential was read, and no route
was changed. The numeric aggregate spend cap is still absent.

The storage checker included the repository, approved data root, Docker WSL
model volume, this hourly automation directory, and all existing Wrench
siblings/legacy roots found in the current host inventory. It reported
`WITHIN_LIMIT`: 15,552,172,911 actual bytes plus 6,603,000 reserved bytes,
15,558,775,911 projected against the 50,000,000,000-byte limit, with no
inventory errors. C: had 143,543,529,472 bytes free. The existing
`WRENCH-GW-STABLE-EVIDENCE-097-20260928` reservation remains active while the
focused verification and accounting are pending.

After writing this report, the same full-root scan still returned
`WITHIN_LIMIT`: 15,552,179,127 actual bytes and 6,603,000 reserved,
15,558,782,127 projected, with no inventory errors. C: had 143,541,723,136
bytes free. The Iteration 097 reservation remains active for the pending
focused test run.

`git diff --check` on the reviewed E0 pipeline source returned exit 0 with only
the repository's existing line-ending warning. No Wrench source or test file
was changed in this report-only continuation.

## Limits and next work

This is a state continuity and fail-closed mechanics change, not a context
compression result. It includes no tokenizer comparison, paired coding task,
verified completion, frontier call, cost receipt, LoRA decision, or sustained
engineering session. The current Wrench frontier-token savings result
remains N/A, and the 95/5 completion/routing, 95% token/cost savings, and
all-day engineering claims remain unproven.

Next, run the two named focused suites only after a fresh 10% RAM/VRAM admission
and confirm the destination/storage reservation. Then measure source-only,
transcript, and stateful-context arms on paired coding episodes with exact
target-tokenizer counts, correctness tests, recovery/retry accounting, and
all-in cost. Keep the stateful path as a deterministic component baseline;
the current model-size lead remains Qwen3.5-2B LoRA for bounded context
decisions, not a proven winner or a standalone coding worker. Fit-03 still
requires an exact review against the current goal hash and at least 25% free
RAM at start. The held-out split stays sealed.
