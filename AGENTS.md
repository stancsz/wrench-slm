# Wrench working agreement

Write naturally. Do not use em dashes.

## Read first

1. [GOAL.md](GOAL.md) and [North Star](docs/northstar/README.md).
2. The [current goal](docs/goal/wrench-v2-realignment/GOAL.md) and relevant reports.
3. [V2 architecture](docs/northstar/V2_ARCHITECTURE.md),
   [experiment](docs/northstar/V2_EXPERIMENT.md), and
   [storage/recovery policy](docs/northstar/STORAGE_AND_RECOVERY.md).

The owner has realigned Wrench to a Layer 1 context runtime and self-learning
LoRA. The v1 pruning and binary-only objectives are superseded. Adapter and
routing design belong to v2. Follow the staged experiment; a design or old
receipt is not authority to start an unbounded training job.

## Storage is a hard boundary

All Wrench-owned data, weights, checkpoints, caches, logs, downloads, temporary
files, generated artifacts, environments, hidden files, Git data and worktrees
must remain **below 50,000,000,000 bytes (50 GB decimal) in aggregate**.
Moving or duplicating them elsewhere does not reset the budget.

Use `C:\wrench-slm-data` with `weights`, `checkpoints`, `datasets`,
`artifacts`, `logs`, and `cache` subdirectories. D: is unavailable on this
host. Keep small source, manifests and curated documentation in the repository.
Set `HF_HOME` and `TORCH_HOME` under the approved root.

Before selecting or downloading a model, enumerate every shard and metadata
file, pin the revision, sum their bytes, and include cache/format duplicates.
Before every download, extraction, training, inference, benchmark, packaging,
delegated job, or other artifact-producing job:

```powershell
python tools/check_wrench_storage_budget.py status
python tools/check_wrench_storage_budget.py reserve --job-id UNIQUE_JOB_ID --reserve-bytes PEAK_ADDITIONAL_BYTES
```

Account for final output, source downloads, unpacked copies, retained
checkpoints, optimizer state, logs and temporary/cache growth that coexist.
Actual use plus all active reservations must stay below the ceiling.
Use `--include-root` for every Wrench path outside the repository and approved
root, including link targets. Check status during long jobs and before each
checkpoint. Release the reservation only after the job stops and final files
are accounted for. Unbounded growth or an incomplete inventory blocks the job.

The checker is job admission, not an OS quota, disk-health test, background
monitor, or automatic kill switch. Check the destination volume's free space
too. Never overwrite the only good data/model copy or silently delete user
data, other tasks' files, active versions or evidence to make room.

## Safety and learning invariants

- The learned controller proposes bounded decisions. It has no arbitrary
  shell, credential access, autonomous code mutation or permission authority.
- Deterministic parsers/indexers may write only authorized, bounded Wrench
  state. Broad shell/test/deployment tools in the notes do not grant their
  execution to Wrench.
- Freeze the foundation and installed Wrench-Core adapter. Train a new personal
  candidate during normal learning. Evaluate, then atomically activate; retain
  a known-good rollback. Follow the full lifecycle in the design.
- Keep mutable facts in external state; learn behavior from reviewed,
  outcome-backed experience. Teacher disagreement and corrections are
  candidate labels requiring checks, not automatic ground truth.
- Never train or tune on sealed final data. Existing exposure issues remain
  quarantined. Preserve rights, consent, redaction, group/time splits, hashes
  and review provenance.
- Never equate synthetic passes, small weights, replay or a classifier score
  with production utility. Record failures and exact tested identities.
- Production enablement, publication and spending require their own authority.
  Old canary/corpus allowances are not v2 allowances.

## Host resources

Before and during training, inference, benchmark, packaging and delegated jobs,
keep at least **10% system RAM and 10% VRAM free**. Inspect the actual device;
past 5070 Ti receipts do not identify the current host. Lower concurrency,
batch/context/cache size or workload footprint if a reserve would be breached.
Stop the job if it cannot remain safe. Never terminate unrelated applications,
Docker services or WSL distributions without user authorization.

## Repository map and checks

- `src/wrench_harness/`: retained worker, verifier, context, router and client code.
- `tools/`, `tests/`, `examples/`: local utilities, checks and examples.
- `docs/northstar/`: product direction; `docs/goal/`: goal tracking.
- `docs/reports/`, `docs/evals/`: task evidence and review.
- `docs/misc/v1/`, `docs/archive/`, `phases/`: legacy contracts/history.
- `site/`: bilingual documentation source; `docs/gh-pages/`: generated site.

Use Python 3.11+. Checks include `python -m pytest` with named focused tests,
`git diff --check`, and the storage checker. The static site uses
`python tools/build_docs_site.py --output PATH` and
`python tools/check_docs_site.py --site PATH`; reserve its output first.

Keep `docs/` free of loose files. Scratch belongs under `tmp/<task>/` or
the approved data root and counts against storage. Preserve unrelated edits.
Archive superseded direction and repair live links; never rewrite historical
evaluation rows or hash-bound receipts. Large deletion, training and deployment
are not repository cleanup.

## Delegation

Default to one agent unless independent work or review materially helps.
Every remote worker payload must be self-contained: unique job ID and nonce,
objective and verification scope, repository and expected commit, artifact
identity/hashes, exact allowed commands and output paths, timeout/retries,
10% RAM/VRAM reserves, no-spend/no-credential boundaries, and response schema.
Wrong-host, missing-nonce or empty sessions are unverified. Preserve the
receipt and use a fresh authenticated session; never promote them to release,
parity or hardware evidence. The old `AGENTS.local.md` queue is historical.
