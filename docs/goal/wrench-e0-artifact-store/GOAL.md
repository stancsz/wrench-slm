# E0 bounded artifact store

Status: bounded store with protected-by-default expiry eligibility implemented; production retention policy, scheduler, and recovery qualification pending
Supervisor: root agent as goal owner
Started: 2026-09-24
Baseline: `36d2d1d89bd4eb3036a3bb2874866fff517d5900`

## Product outcome

Provide a small local persistence primitive for exact source evidence. A caller
supplies bytes and binds them to snapshot, path, and content identity. The store
keeps content-addressed objects under an explicit dedicated root, supports
request-scoped pins, and returns explicit missing, evicted, or corrupt results.
The store primitive does not orchestrate other runtime modules. A separate
caller-owned preparation facade composes it with snapshot and context helpers.
The store never searches for sources, chooses a default directory, or invokes
a model.

## Acceptance

- Bound object bytes, unique object count, manifest bytes/entries, staging files,
  and aggregate store bytes.
- Stage writes on the store volume; verify hashes before publishing objects;
  atomically replace current and previous manifests.
- Reopen validates manifests and referenced objects. Restore the previous
  manifest only when its bytes and objects verify; otherwise report corruption.
- Keep process-local request pins from eviction. Evict in deterministic order,
  record bounded tombstones, and delete only recognized objects after both
  manifest slots stop referencing them. The eviction pass may delete only the
  selected eligible object hashes; pre-existing unreferenced blobs remain for
  separate recovery review.
- Default new source records to protected with no expiry. Make disposable
  classification explicit and require its expiry timestamp. Eviction requires
  an explicit UTC epoch cutoff and selects only expired, unpinned disposable
  content whose every manifest reference is also eligible. Return without
  mutation when the eligible blobs cannot meet the requested byte target.
- Read legacy v1 manifests with all records normalized to protected. Write v2
  retention metadata without changing artifact handle identity; repeated puts
  cannot silently downgrade or rewrite an existing retention decision.
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
| Integrate and commit this bounded store slice | Complete | Commit `c6eba5f` |
| Connect to snapshots/context and continue E0 | Accepted for local preparation | [E0 caller-owned pipeline](../wrench-e0-context-pipeline/GOAL.md); production request manager and recovery qualification remain outside this slice |
| Enforce safe retention eligibility in the bounded store | Implemented; caller policy remains pending | [Retention eligibility report](../../reports/wrench-e0-artifact-store/retention-eligibility.md); expiry-aware manual eviction does not set real-data retention periods |
| Add regression evidence for migration and eviction recovery boundaries | Focused tests pass; review recorded | [Recovery regression report](../../reports/wrench-e0-artifact-store/recovery-regressions.md) and [independent evaluation](../../evals/wrench-e0-artifact-store/recovery-regressions-review.md) |
| Enforce physical-volume headroom before bounded object and manifest staging writes | Cooperative per-write guard and focused suite reviewed; hard 5 GB guarantee remains open | [Headroom guard report](../../reports/wrench-e0-artifact-store/headroom-guard.md) and [evaluation](../../evals/wrench-e0-artifact-store/headroom-guard-review.md) |
| Recover a valid previous generation when the current manifest exceeds its configured size limit | Implemented and reviewed; bounded test module passes with three existing symlink-permission skips | [Recovery hardening report](../../reports/wrench-e0-artifact-store/recovery-hardening.md) and [evaluation](../../evals/wrench-e0-artifact-store/recovery-hardening.md); commit `ef1fa3b` |

## Limits

This slice does not implement a durable request manager, cross-process lock,
power-loss proof, namespace registry, retention schedule, automatic cleanup,
deletion-rights workflow, or production store integration. Source artifacts
written by current production call sites remain protected indefinitely unless
a future caller explicitly opts into a reviewed expiry policy. No real-data
retention duration is selected here. Same-disk previous manifests do not
protect against volume loss. Production qualification remains open in the v2
experiment.

The save-time headroom guard is a per-write check using the store root's
physical volume free bytes. It does not reserve space across a full put or
coordinate with other writers, so free space can change after a successful
probe. Store-directory creation during initialization precedes the first
manifest probe. This is separate from the cooperative 50 GB aggregate
admission checker and does not prove a hard physical reserve.
