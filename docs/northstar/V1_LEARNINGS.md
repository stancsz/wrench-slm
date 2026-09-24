# V1 incident and lessons for v2

Recorded: 2026-09-23 (America/Edmonton)

## What happened and what we know

The owner reports that the first Wrench attempt ended with filesystem
corruption and lost data, following a model-reduction/training effort described
as pruning a 27B model toward 4B. The owner requires checking total model size
and keeping all Wrench weights and artifacts below 50 GB.

Treat corruption and data loss as the owner's incident account. The surviving
repository does not contain incident-time disk telemetry, a filesystem repair
report, a device-health diagnosis or a recovered original artifact establishing
the physical cause. Missing D: paths show unavailable payloads on this host,
not proof that disk exhaustion caused filesystem corruption. A full disk can
cause failed/partial writes; the incident's causal chain remains unknown.

The [direction snapshots](../archive/2026-09-23-v1/README.md) retain the
4.25B/pruning context, bounded-worker work, binary-head experiments and separate
25k corpus attempt. These were different phases; failure of the last corpus
does not mean no earlier fitting occurred.

## Surviving evidence

- The [dataset state audit](../reports/wrench-25k-data/dataset-state-audit.md)
  recorded zero admitted training/development/final rows for the proposed
  25k corpus and unavailable historical D: payloads.
- [Phase 447](../../phases/phase-447-wrench-training-data-corpus/README.md)
  recorded 402 authored drafts, zero quality-gated admissions and unresolved
  possible sealed-final exposure. Draft counts do not establish recoverability.
- The audit recorded a validator crash and a mismatch between current source
  identity and a prior passing receipt. Later repair notes survive in that
  audit. Old passes cannot validate a different executable.
- The [classifier evidence](../../phases/system-one-readiness-20260922/README.md)
  and [later fitting record](../../phases/system-one-authorized-training-20260923/README.md)
  show holdout degradation, unsafe continuations, label errors and posthoc
  regression work. They do not establish productive deployment.

These findings support a restart with better controls. They do not prove that
pruning caused disk loss or that a new foundation solves data/evaluation errors.

## Changes that carry into v2

| Lesson | Required change | Evidence before relying on it |
| --- | --- | --- |
| Total footprint exceeds the headline model size | Pin every shard, cache, conversion and peak training state | Byte manifest, reservation and destination free-space check |
| A sole mutable copy is a failure point | Immutable datasets/base/core and new adapter candidates | Hash verification, interrupted-write recovery and restored prior version |
| Checkpoints and logs can grow without bound | Byte/version retention, live reservation, checks before saves | Accounted peak below 50 GB; no silent removal of needed state |
| A manifest cannot replace a lost payload | Admit only present, verified and recoverable data | Source hashes and restore/reload drill |
| Synthetic templates can create misleading scores | Group/time/repository holdouts, exact oracles and reviewed outcomes | Fresh evaluation and matched real workflows |
| A teacher answer or correction can be wrong | Keep candidate labels until outcomes support them | Independent verification, review and lineage |
| Final data reuse invalidates a fresh claim | Isolate sealed data; quarantine unresolved exposure | Access/leakage audit against frozen splits |
| Many phases can hide the direction | One North Star/current goal and archived old instructions | Fresh-agent navigation and independent review |

The [storage and recovery rules](STORAGE_AND_RECOVERY.md) apply across all
Wrench locations. An artifact budget is not a filesystem integrity guarantee
or a backup system.

## What v2 changes experimentally

Start from a native small Qwen checkpoint. Put product behavior in a core
adapter and local learned behavior in a separate personal adapter. Keep facts
in deterministic indexes and source state. Add learned choices individually
against a deterministic baseline. Each personal update must pass authority and
regression gates plus a fresh personalization evaluation before activation.

Replay may reduce forgetting; it does not eliminate forgetting or make adapter
composition harmless. Removing the personal adapter must restore verified core
behavior. Interrupted promotion must recover safely. These are requirements,
not implemented capabilities.

## Recovery boundary

This cleanup preserves surviving source, receipts, edits and design notes.
It does not recover missing D: payloads or repair the filesystem. Unknown
artifact integrity requires quarantine. Today's 5060 Ti and free-space
observations do not establish the historical failure's cause.
