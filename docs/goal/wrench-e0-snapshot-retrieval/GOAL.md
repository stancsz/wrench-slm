# E0 snapshot identity and exact-source retrieval

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
| Review path, hash, and resource failure cases | Accepted | `docs/evals/wrench-e0-snapshot-retrieval/review.md` |
| Integrate and commit this increment | Complete | Commit `b23f925` |
| Run POSIX pytest fixtures | Complete | Ubuntu 24.04 WSL: snapshot and artifact-store suites, 42 passed, 2 skipped |

## Next E0 work after this slice

The bounded artifact store, snapshot/context bridges, namespace registry,
serialized prompt gate, structural index, outcome receipt, and caller-owned
preparation facade now exist as separately accepted slices. Full E0 acceptance
remains open: runtime-matched prompt/tokenizer identity, complete lifecycle
accounting, and end-to-end authority evidence still need evidence. E4
matched-task utility across the three clients remains a separate open gate.
Keep E1-E4 adapter, learning, and recovery gates open until their evidence
exists.
