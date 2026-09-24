# E3 synthetic model-version lifecycle

Status: accepted bounded synthetic development primitive; production E3 gates remain open
Supervisor: learning lifecycle supervisor, under root integration authority
Job: `W2-NS-E3-SYNTHETIC-VERSION-LIFECYCLE-20260924`
Nonce: `E3SYN-ROOT-7C12`

## Outcome

Implement a small, local development primitive for immutable model-version
manifests and lifecycle transitions. This bounded slice prepares the E3
control plane using synthetic opaque IDs and tiny bytes. It does not load a
model or claim runtime compatibility, training, E1/E2 acceptance, or production
recovery.

## Acceptance

- Store version artifacts under an explicit root with bounded file, manifest,
  version-count, 512-entry, and 10,000,000-byte aggregate limits. Check
  projected writes and reject unsafe paths, reparse components, and unexpected
  or orphan entries without removing them. Bind immutable version manifests
  to content hashes and compatibility identity fields.
- Hard-code `training_eligible=false` and `production_activation=false` in
  emitted state/receipts. Lifecycle activation is development-only.
- Admit a complete candidate only when its base/core identity and required
  compatibility fields match the retained version. Reject missing, corrupt,
  incompatible, or incomplete files before changing active state. Require an
  exact receipt bound to candidate ID, manifest digest, parent, and development
  flags when an active candidate is opened or pinned.
- Atomically activate an admitted version while preserving factory and prior
  version references. A request pins an immutable version handle; activation
  must not change the version seen by an in-flight request.
- Support verified rollback and personal-adapter reset to base plus core,
  preserving the factory version and its identities.
- Reopen after restart by verifying referenced files and resolving active or
  prior recovery state. Serialize writers with an OS-backed lock and reject
  stale generations. Preserve a verified backup while recovering corrupt,
  oversized, or parseable-invalid main pointers. Fail closed if neither
  complete generation verifies.
- Exercise activation, a request pin held across activation, candidate
  rejection, failed promotion, interruption, reopen, rollback, and reset with
  tiny synthetic fixtures under the approved data root.
- Record independent review, exact verification command/result, and limits in
  the task report and evaluation.

## Scope and authority

Allowed implementation files are `src/wrench_harness/model_lifecycle.py` and
`tests/test_model_lifecycle.py`. This goal also owns its report, evaluation,
and this goal file. Root owns the shared goal index.

Do not use network, providers, model or data downloads, credentials, customer,
participant or repository task data, client integrations, model loading,
training, inference, or production routes. No dependency installation or
commits are part of this task. Keep all test scratch beneath
`C:\wrench-slm-data\tmp\W2-NS-E3-SYNTHETIC-VERSION-LIFECYCLE-20260924`.
Keep the total Wrench footprint below 50 GB and at least 10% system RAM and
VRAM free during delegated and test work.

## Ownership and remaining gates

The implementer owns only the module and focused tests. The supervisor
integrated and recorded the report/evaluation and goal status. Independent
review passed for the recorded source/test hashes. Root reviews the integrated
result and owns its commit and goal-index link.

This synthetic component cannot activate a production model. Actual runtime
compatibility, local model identity, dual-adapter parity, consented experience
capture and label lineage, utility, independent-backup recovery, and any
production activation remain separate gates under the v2 experiment and human
authority. The symlink fixture skipped because the Windows host did not permit
link creation. Review and tests do not establish power-loss or volume-loss
durability, and filesystem races with non-cooperating writers remain outside
the evidence.

## Repair follow-up

Root authorized a bounded repair at base HEAD
`cbd819d324bcc571af5116c6a40b3f58519d375d`. Exact-byte receipt validation now
rejects wrong JSON flag types and duplicate keys. Startup can recover to a
verified previous version when an active candidate receipt is malformed, and
candidate admission and activation verify the current active manifest hash and
payloads before promotion. The stale-reset review finding did not apply to this
base because `reset_personal` already used the serialized-writer guard; a new
regression confirms a stale instance cannot reset over a later activation.

The repaired source and tests passed the focused suite with **26 passed, 1
skipped** and passed `git diff --check`. Independent review passed on the exact
source/test hashes; see the [repair evaluation](../../evals/wrench-e3-synthetic-version-lifecycle/implementation.md#repair-follow-up-evaluation)
and [repair report](../../reports/wrench-e3-synthetic-version-lifecycle/implementation.md#repair-follow-up).
The symlink fixture remains skipped on this Windows host. Root retains commit
and shared-index ownership. Production E3 acceptance remains open.

At base HEAD `3982b0fd1ca984da44e1adfb1100cb7b69d7c7c8`, reinspection found
`reset_personal` already guarded by `@_serialized_writer`. A dedicated
cross-process regression now pauses reset while holding the OS lock and proves
a second process cannot activate from its stale generation over the reset.
The focused regression passed; exact evidence, storage/resource readings, and
the independent review disposition are in the [reset serialization report](../../reports/wrench-e3-synthetic-version-lifecycle/implementation.md#reset-serialization-regression-follow-up).
