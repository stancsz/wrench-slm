# Wrench v2 direction and repository realignment

Status: complete for direction, cleanup and experiment definition
Updated: 2026-09-23 (America/Edmonton)
Owner: root agent as orchestrator and supervisor, under human product authority

## Original outcome

Realign Wrench as a Layer 1 context runtime with self-learning LoRA. First
clean up the repository, record why v1 ended with owner-reported filesystem
corruption/data loss, and explain experiment v2 using both supplied notes.
Preserve the strict total limit below 50 GB and surviving useful work.

This goal delivers the direction, cleanup and experiment definition. It does
not claim that the full v2 runtime or training is implemented. The full product
end state remains [E0 through E4](../../northstar/V2_EXPERIMENT.md).

## Requirements and acceptance evidence

| Requirement | Deliverable | Completion evidence |
| --- | --- | --- |
| Read and preserve both owner notes | [Inputs](../../northstar/inputs/README.md) | Exact attachment hashes and complete local copies |
| Credible customer/value/sustainability thesis | [North Star](../../northstar/README.md) | Specific user/job, alternatives, value proof, assumptions |
| Layer 1 runtime plus all three weight components | [Architecture](../../northstar/V2_ARCHITECTURE.md) | W0-W5; immutable base/core; bounded personal learning and recovery |
| Explain v1 failure without invented forensic conclusions | [V1 learning](../../northstar/V1_LEARNINGS.md) | Owner account, supporting audits, known/unknown cause and controls |
| Concrete v2 experiment | [Experiment](../../northstar/V2_EXPERIMENT.md) | Stages, matched arms, split discipline, metrics, stop criteria and next work |
| Total footprint below 50 GB | [Storage policy](../../northstar/STORAGE_AND_RECOVERY.md) and model manifest | Fresh status, exact boundary check, complete upstream byte metadata |
| Clean active repository guidance and preserve history | Root README/GOAL/AGENTS, goal index, legacy relocation and archive | No loose docs files, working links, archived hashes and scope reconciliation |
| Useful source retained and gaps explicit | [Reuse audit](../../reports/wrench-v2-realignment/reuse-audit.md) | Independent source inspection; no false implemented claims |
| User edits and evidence survive cleanup | Snapshot manifest, scoped edits | Historical payloads unchanged; pre-existing source edits retained |
| Honest review and verification | [Evaluation](../../evals/wrench-v2-realignment/review.md) | Independent critique, applicable local checks and repaired findings |

## Ownership and current tasks

Root owns shared documents, integration and final acceptance. The independent
worker `v1_evidence_audit` completed a read-only source/evidence audit. Root
persists its findings. A separate fresh review covered the integrated result and returned PASS after
two minor documentation repairs.
Neither worker may change source, access sealed data, train, spend or publish.

| Task | Status |
| --- | --- |
| Read notes, inspect repository and preserve prior state | Complete |
| V1 evidence/reuse audit | Complete |
| Architecture, experiment, lessons and storage direction | Complete |
| Navigation cleanup, current contract and site status | Complete |
| Local checks, independent critique, repair and completion audit | Complete |

## Bounds

Preserve historical source, receipts, datasets and unrelated edits. Keep
reversible archival copies of replaced direction documents. No model download,
training, inference, paid API call, filesystem repair, destructive deletion,
production routing, commit or publication belongs to this cleanup.

The parent contract now represents v2 realignment with no v2 paid allowance.
Old corpus and canary authorizations are archived at their original identities;
they cannot be rebound to v2 or silently expanded.

Root reserved 20,000,000 peak additional bytes for documentation, bounded
verification and site output under `wrench-v2-realignment-20260923`.
Every later artifact job still requires a fresh status/admission. Preserve
10% free RAM/VRAM and the strict 50 GB aggregate ceiling.

## Next action and completion boundary

The [completion audit](../../evals/wrench-v2-realignment/review.md) records
observed checks, repaired findings and independent acceptance. This
realignment is complete. E0 preparation slices have since been implemented and
accepted, but the E0 milestone is not accepted. Exit still requires
runtime-matched prompt and tokenizer identity, complete deterministic-baseline
accounting, authority-scoped rule/no-model route and zero-unauthorized-action
evidence, and POSIX-host snapshot follow-up. Matched-task utility and full
request-lifecycle accounting remain later E4 gates. Keep E1-E4 staged behind
their defined gates. The continuous LoRA remains a required later stage of the
full v2 experiment. A ten-case Wrench-authored synthetic matched-task seed now
checks route mechanics and source-derived task oracles; see the [seed report](../../reports/wrench-e0-synthetic-matched-tasks/seed.md)
and [independent evaluation](../../evals/wrench-e0-synthetic-matched-tasks/review.md).
This open development fixture is not utility evidence or E0 acceptance.
