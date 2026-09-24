# E0 bounded artifact store

Status: accepted standalone implementation increment; integration pending
Supervisor: root agent as goal owner
Started: 2026-09-24
Baseline: `36d2d1d89bd4eb3036a3bb2874866fff517d5900`

## Product outcome

Provide a small local persistence primitive for exact source evidence. A caller
supplies bytes and binds them to snapshot, path, and content identity. The store
keeps content-addressed objects under an explicit dedicated root, supports
request-scoped pins, and returns explicit missing, evicted, or corrupt results.
It never searches for sources, chooses a default directory, invokes a model, or
integrates with another runtime module.

## Acceptance

- Bound object bytes, unique object count, manifest bytes/entries, staging files,
  and aggregate store bytes.
- Stage writes on the store volume; verify hashes before publishing objects;
  atomically replace current and previous manifests.
- Reopen validates manifests and referenced objects. Restore the previous
  manifest only when its bytes and objects verify; otherwise report corruption.
- Keep process-local request pins from eviction. Evict in deterministic order,
  record bounded tombstones, and delete only recognized objects after both
  manifest slots stop referencing them.
- Treat leftover staging files as incomplete and retain them without promotion
  or deletion. Reject unknown root/store entries without deleting them.
- Validate every existing component from the filesystem anchor through the
  explicit store root with `lstat` and reparse-point checks. Create missing
  components one at a time, only after validating their parents.
- Tests use bounded temporary fixtures, no object over 1 MiB, and exercise
  exact reads, identity, limits, pins, eviction, interruption recovery, and
  corruption.
- Document single-instance/process-local concurrency and the limits of
  atomic rename and same-volume recovery.

## Tasks and progress

| Task | Status | Evidence |
| --- | --- | --- |
| Implement bounded content-addressed persistence | Complete | `src/wrench_harness/artifact_store.py` and focused tests |
| Review quotas, recovery, path boundaries, pins, and eviction | Accepted with documented limits | `docs/evals/wrench-e0-artifact-store/review.md` |
| Integrate, commit, and identify the next E0 gate | In progress | This goal and [goal index](../README.md) |

## Limits

This slice does not implement a durable request manager, cross-process lock,
power-loss proof, namespace registry, retention scheduler, or production store
integration. Same-disk previous manifests do not protect against volume loss.
Production qualification remains open in the v2 experiment.
