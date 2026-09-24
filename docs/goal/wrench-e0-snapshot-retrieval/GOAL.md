# E0 snapshot identity and exact-source retrieval

Status: accepted bounded implementation increment; POSIX pytest follow-up pending
Supervisor: root agent as goal owner
Started: 2026-09-23 (America/Edmonton)
Baseline: `380c799f3199e08404908ecd6f7faa7496992367`

## Product outcome

Let the deterministic context runtime identify caller-selected local sources by
stable snapshot and content hashes, retrieve their exact bytes when unchanged,
and fail with explicit missing or stale results when they no longer match. This
advances E0's snapshot and exact-source contract without copying sources into
an unbounded cache or store.

This is the next slice in the full v2 experiment, not all of E0 or production
qualification. Customer/value proof, full E0-E4 requirements and data rules
remain in the [North Star](../../northstar/README.md),
[architecture](../../northstar/V2_ARCHITECTURE.md), and
[experiment](../../northstar/V2_EXPERIMENT.md).

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

Follow the [storage/recovery policy](../../northstar/STORAGE_AND_RECOVERY.md):
strictly below 50 GB aggregate, fresh reservation before artifact-producing
work, at least 5 GB destination-volume headroom, and 10% RAM/VRAM reserve for
resource-intensive jobs. This slice must stay in memory and use bounded test
fixtures. Do not scan the full repository, download, infer, train, spend,
publish, deploy, collect user traces, or mutate source files through the runtime.

## Tasks and progress

| Task | Status | Evidence |
| --- | --- | --- |
| Implement bounded source manifest and verified exact reads | Complete | `src/wrench_harness/snapshot.py` and focused tests |
| Review path, hash, and resource failure cases | Accepted with POSIX pytest caveat | `docs/evals/wrench-e0-snapshot-retrieval/review.md` |
| Integrate, commit, and choose next E0 gap | In progress | This goal and [goal index](../README.md) |

## Next E0 work after this slice

The reversible bounded artifact store, namespace discovery, exact serialized
prompt accounting, and verified outcome receipts remain unimplemented. Continue
the full E0 baseline before considering E1 model work. Keep E1-E4 adapter,
learning, recovery, and matched-utility gates open until their evidence exists.
