# E0 snapshot identity and exact-source retrieval
> Supporting record only. Follow the [active goal](../wrench-token30/GOAL.md);
> this file's next-step text has no authority unless that goal's checkpoint
> adopts it as an evidenced dependency or the owner sets a new commitment.


Status: committed bounded implementation increment; POSIX pytest follow-up complete
Supervisor: root agent as goal owner
Started: 2026-09-23 (America/Edmonton)
Baseline: `380c799f3199e08404908ecd6f7faa7496992367`

## Product outcome

Let the deterministic context runtime identify caller-selected local sources by
stable snapshot and content hashes, retrieve their exact bytes when unchanged,
and fail with explicit missing or stale results when they no longer match. This
advances E0's snapshot and exact-source contract without copying sources into
an unbounded cache or store.

This is a historical component record, not an active slice in an E0-E4
experiment. Current work follows the [active objective](../wrench-token30/GOAL.md).

## Acceptance

- A caller supplies a root and an explicit finite list of relative source paths.
  No directory traversal, model, provider or external service is used.
- A deterministic manifest records normalized path, exact size and SHA-256 per
  source, plus a snapshot hash independent of input ordering.
- Exact retrieval is read-only and returns original bytes only after rechecking
  source identity. Missing, changed, unsafe and unknown handles produce
  explicit failure states and never substitute current unverified bytes.
- Path escape, symlink ambiguity, duplicates, non-regular files, oversized
  files, excessive file counts and aggregate byte growth fail closed.
- Focused tests cover exact round-trip, snapshot determinism, modified/missing
  sources and admission/path failures. Changes receive independent review,
  documentation, and a scoped commit.
- No source copies or persistent indexes are produced. The later reversible
  artifact store remains a separate E0 requirement.

## Constraints

Follow the [storage/recovery policy](../../operations/STORAGE_AND_RECOVERY.md):
strictly below 50 GB aggregate, fresh reservation before artifact-producing
work, at least 5 GB destination-volume headroom, and 10% RAM/VRAM reserve for
resource-intensive jobs. This slice must stay in memory and use bounded test
fixtures. Do not scan the full repository, download, infer, train, spend,
publish, deploy, collect user traces, or mutate source files through the runtime.

## Tasks and progress

| Task | Status | Evidence |
| --- | --- | --- |
| Implement bounded source manifest and verified exact reads | Complete | `src/wrench_harness/snapshot.py` and focused tests |
| Review path, hash, and resource failure cases | Accepted | `docs/evals/wrench-e0-snapshot-retrieval/review.md` |
| Integrate and commit this increment | Complete | Commit `b23f925` |
| Run POSIX pytest fixtures | Complete | Ubuntu 24.04 WSL: snapshot and artifact-store suites, 42 passed, 2 skipped |

## Historical E0 gates

The bounded artifact store, snapshot/context bridges, namespace registry,
serialized prompt gate, structural index, outcome receipt, and caller-owned
preparation facade now exist as separately accepted slices. Full E0 acceptance
remains open as historical product gates. They are not the current work queue.
Use this component only when the [active goal](../wrench-token30/GOAL.md)
checkpoint names it as an evidenced dependency; matched-task utility is now
judged by that goal's paired-comparison criteria.
