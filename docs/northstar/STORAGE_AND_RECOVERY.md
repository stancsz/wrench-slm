# Wrench storage and recovery policy

Owner ceiling: **strictly below 50,000,000,000 bytes (50 GB decimal)**.

## Admission and total model size

Inventory the checkout, all worktrees, hidden/ignored files, Git, environments,
Wrench-attributable caches, datasets, weights, versions, logs, stores, temporary
extraction and conversions. Copies elsewhere remain in the Wrench budget.
Include linked targets and external locations the checker cannot discover.

Before model selection, pin the upstream revision and enumerate every file:
all weight shards, tokenizers and configs. Record published byte sizes;
parameter labels and adapter size alone are insufficient. Verify downloaded
hashes and bytes before loading. Unknown totals block admission.

Before each artifact-producing job, run storage status, then reserve peak
additional bytes under a unique job ID. Bound every output. Include coexisting
downloads, extracted copies, cache, conversions, optimizer/training state,
checkpoints and logs. Keep the reservation until the process stops and files
are accounted for.

For each destination volume, also require free space for the reserved peak
plus an operating reserve. Initial v2 policy leaves at least **5 GB physically
free after projected writes**. This is separate from the aggregate Wrench
ceiling. Check it before and during long jobs.

## Operating envelopes

Planning maxima, not current use or permission to fill them:

| Category | Decimal GB |
| --- | ---: |
| One foundation snapshot and metadata | 4 |
| Core and personal active/previous/candidate adapters | 2 |
| Repository indexes and reversible artifact store | 12 |
| Reviewed data, experience and replay | 6 |
| Source, Git/worktrees, environments and reusable caches | 8 |
| Additional training/download/conversion temporary space | 6 |
| Logs, manifests and recovery material | 2 |
| **Planned maximum** | **40** |

Remaining space is contingency below the strict 50 GB ceiling, not a second
budget. Count conservatively if sharing is uncertain. Every job still needs
measured admission; estimates cannot override the gate.

Retain personal active, previous known-good and at most one candidate.
Retain at most two required core versions during upgrades. Protect source
data and evaluation evidence. If required versions cannot fit, stop growth;
never delete the only recoverable good state.

## Required v2 write and recovery protocol

1. Keep foundation, installed core, admitted datasets and active personal
   adapter immutable. Each candidate gets a new version directory.
2. Write within a same-volume staging location with a declared byte maximum.
   Flush/close, verify hashes/size and validate the format.
3. Write a manifest binding base/core/personal hashes, tokenizer/runtime,
   data splits, parent version, metrics and resource receipt.
4. Validate composition, regression and authority. Incomplete candidates
   cannot become active.
5. Atomically replace a small active-version manifest. In-flight requests
   retain their starting version; later requests use the new one.
6. At startup, verify references. Recover the previous known-good version or
   base+core on missing/corrupt state and record failure. Never silently load
   a partial candidate.
7. Exercise interrupted saves/promotion, missing/corrupt files, exhausted
   reservations and rollback in a bounded directory. Atomic rename alone
   does not prove power-loss durability.

Hashes detect changes; they cannot recreate missing bytes. Before training,
retain a recoverable copy of irreplaceable admitted data, manifests and required
good adapters at an approved failure-independent location. Count backup bytes
in the same aggregate budget. Same-disk copies cannot cover whole-volume
failure. Such recovery storage and a restore drill remain unproven for v2.

Source facts have snapshot hashes and invalidation rules. Evict only unpinned,
expired disposable artifact records under a documented retention policy.
Live context handles pin exact sources through request completion. Stale or
evicted handles return explicit misses and trigger retrieval/escalation.

## Current enforcement and limits

[check_wrench_storage_budget.py](../../tools/check_wrench_storage_budget.py)
scans configured roots and performs cooperative reservations. It rejects
actual plus reserved bytes at or above 50 GB. It does not police every write,
enforce physical-volume headroom, follow arbitrary links, diagnose disk
health or monitor processes. Missing roots currently contribute zero bytes;
detecting a missing expected root and blocking the job is still a manual
admission responsibility, not behavior enforced by this checker.

The v2 job runner and stores still need save-time limits, headroom checks,
bounded retention and recovery. Until implemented, use only explicitly bounded
jobs with admission and monitoring. A missing/unreadable expected root is an
inventory failure, not free capacity. Stop on unbounded growth or write/hash
failures.
