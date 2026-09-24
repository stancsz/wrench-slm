# E1–E3 learning lifecycle readiness audit

Job: `W2-NS-E1-E3-LIFECYCLE-GAP-AUDIT-20260926`

Nonce: `E1E3-SUP-4A28`

Audit baseline: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`

Review date: 2026-09-24

## Scope and method

This is a read-only source and evidence review of E1 core-adapter readiness, E2
experience capture and personal-adapter readiness, and E3 activation and
recovery. Three workers reviewed disjoint scopes. They did not edit files, run
tests or code, access datasets, load models, or create artifacts. At review
completion the shared branch had advanced to
`4d692f3a796abcb75b30ca572a2597657ce000c8`; the reviewed E1/E2/E3 source and
North Star files were unchanged between that commit and the audit baseline.
The concurrent working-tree edits were preserved.

Admission was checked before writing this report: the 5,000,000-byte audit
reservation was active, the storage checker reported `WITHIN_LIMIT` with
`C:\Users\stanc\AppData\Local\npm-cache` included, and measured free system
RAM and VRAM were above 10%. This documentation is the only artifact produced
by this job. No model, data, or performance result is claimed.

## Findings

### E1: pinned-model runtime and core adapter

**Implemented primitive:** `candidate_identity.py` validates a bounded local
file set against supplied pinned metadata and can issue a receipt scoped to
local file identity only. Synthetic filesystem fixtures cover mechanics. The
metadata manifest pins `Qwen/Qwen3.5-0.8B` revision
`2fc06364715b967f1860aea9cf38778875588b17`, but explicitly says weights have
not been downloaded and published sizes are not local verification.

**Missing or unproven:** local foundation bytes and verified complete size;
runtime qualification for that revision; actual dual-adapter support; a
Wrench-Core artifact and identity; core/personal compatibility binding;
numerical two-adapter composition, frozen-parameter, save/load and rollback
parity on the selected backend; curated-core training and held-out improvement
against E0. Legacy calibration utilities have single-adapter/probe mechanics,
not this v2 contract. E1 is not ready for training or acceptance.

### E2: permitted experience capture and label lineage

**Implemented primitive:** `synthetic_experience_record.py` builds a bounded,
content-free comparison for one case in the fixed authored fixture. It records
digests and match/mismatch/unknown, fixes scope to open development, sets
consent to not applicable for synthetic material, and hard-codes
`training_eligible=false`. Synthetic fixture admission is narrow and requires
the fixture's pinned identity and mechanics review.

**Missing or unproven:** opt-in capture at the task/session boundary;
withdrawal and deletion propagation; redaction evidence; rights/consent
versioning; reviewed labels tied to independent verifiers and source/outcome
identity; a bounded persistent experience buffer; replay curation and
repository/task/time splits; asynchronous personal-LoRA fitting with base and
core frozen. The E0 receipt join accepts caller-supplied claims and does not
observe client activity, persist experience, prove task truth, or establish
consent. Legacy binary intake is not a v2 substitute. E2 is not ready for
collection or fitting.

### E3: candidate activation, reset, and recovery

**Implemented primitive:** `ArtifactStore` has bounded objects and manifests,
hash-checked reads, current/previous manifest recovery, explicit corruption
handling, and process-local request pins for source artifacts. Router state
also supports config-bound save/load/reset for circuit-breaker state.

**Missing or unproven:** an adapter/model-version manifest; atomic activation
of an evaluated candidate; per-request pinning of the active base/core/
personal version; retained factory and prior adapter references; startup
verification and fail-closed recovery for model references; personal-adapter
reset/deletion and core-version compatibility checks; interruption, restart,
corruption, missing-file and rollback tests for adapter activation. The
artifact store's manifest and pins serve source artifacts, while router reset
does not reset learning state. E3 is not ready for activation or acceptance.

## Exact sources examined

Line numbers refer to the audited shared revision unless stated otherwise.

- Product and stage requirements: `docs/northstar/V2_ARCHITECTURE.md:62-87,105-137`;
  `docs/northstar/V2_EXPERIMENT.md:38-42,73-88,138-147`;
  `docs/northstar/STORAGE_AND_RECOVERY.md:52-75`.
- Candidate and E1 evidence: `docs/northstar/model-candidate.json:2-10,98-101`;
  `src/wrench_harness/candidate_identity.py:778-850`;
  `src/wrench_harness/worker.py:275-322`;
  `tools/calibrate_qwen_router.py:25-90,165-200,228-265`;
  `docs/goal/wrench-e1-candidate-identity/GOAL.md:9-38`;
  `docs/evals/wrench-e1-candidate-identity/review.md:9-15,49-65`.
- Experience and E2 evidence: `src/wrench_harness/synthetic_experience_record.py:163-201,204-333`;
  `src/wrench_harness/synthetic_fixture_admission.py:31-115`;
  `src/wrench_harness/e0_request_record.py:1-5,33-43,98-127`;
  `tools/intake_system_one_real_requests.py:1-5,42-88,106-152`;
  `docs/goal/wrench-northstar-pilot-readiness/GOAL.md:18-20,99-122`;
  `docs/evals/wrench-e0-synthetic-matched-tasks/experience-record.md:19-37`.
- Recovery and E3 evidence: `src/wrench_harness/artifact_store.py:197-239,318-341,462-566,686-732,814-872`;
  `tests/test_artifact_store.py:197-230,431-475`;
  `src/wrench_harness/state.py:12-39`;
  `src/wrench_harness/router.py:17-28,93-109`;
  `tests/test_router_state.py:41-100`.

The test files and existing reports were inspected as evidence records only;
no test suite was run for this audit.

## Recommended next engineering increment

Implement a separate, bounded model-version lifecycle component using synthetic
opaque artifacts only. Bind each immutable version manifest to foundation,
core, personal, runtime, tokenizer, compatibility and content hashes; pin one
version handle for each request; stage and verify candidates before atomically
switching the active manifest; retain prior/factory references; and provide an
explicit personal-adapter reset to base plus core. Fail closed on missing,
corrupt, incomplete or incompatible references. Exercise save interruption,
restart, concurrent request pins, failed promotion, rollback and reset with
small synthetic files. Do not load a model or make quality claims in this
slice.

Dependencies are the current bounded storage/recovery primitives and a
manifest contract coordinated with the E1 candidate identity verifier. The
component must keep unknown runtime or adapter compatibility unverified and
refuse activation until E1 supplies those verified identities. Acceptance
evidence is a reviewed manifest/state-transition contract plus fixtures that
show incomplete or corrupt candidates never activate, requests keep their
starting version, restart returns the valid active/prior version, and reset
removes the personal reference while preserving base/core identities.

Human-only gates remain: approval of any actual model acquisition and runtime
load/training; task- and participant-level consent plus retention, withdrawal,
redaction and deletion terms before E2 data capture; approval of any production
activation or publication. Synthetic lifecycle mechanics do not pass E1/E2
utility or E3 production recovery gates.
