# Model storage retention hold

Updated: 2026-09-10

The current explicit retained set is over the 5,000,000,000-byte budget. The
measurement receipt is `artifacts/model-release/storage-audit-20260910.json`.
No deletion or archive move has been performed.

| Retained group | Bytes |
| --- | ---: |
| Base dependency | 999,586,347 |
| V20 package | 51,196,072 |
| V21 package | 51,275,222 |
| Three V21 snapshots | 3,436,398,552 |
| Three V22 snapshots | 3,436,398,535 |
| Total | 7,974,854,728 |

The overage is 2,974,854,728 bytes. Each trainer snapshot is about 1.145 GB,
so removing one or two snapshots is not sufficient. Removing all three V21
snapshots would leave approximately 4.538 GB; removing all three V22 snapshots
would leave approximately 4.538 GB. Those are retention choices, not automatic
cleanup instructions, because each choice changes which rollback evidence is
locally available.

## Exact dry-run outcomes

These are arithmetic projections from the receipt. They do not move or delete
anything.

| Option | Projected retained bytes | Budget headroom | Evidence tradeoff |
| --- | ---: | ---: | --- |
| Keep everything | 7,974,854,728 | -2,974,854,728 | Retains all local rollback snapshots; over budget |
| Remove V21 snapshots only | 4,538,456,176 | 461,543,824 | Retains V22 development checkpoints; removes V21 rollback checkpoints |
| Remove V22 snapshots only | 4,538,456,193 | 461,543,807 | Retains V21 release checkpoints; removes failed V22 rollback checkpoints |
| Remove both V21 and V22 snapshots | 1,102,057,641 | 3,897,942,359 | Retains base and packages only; removes all trainer rollback checkpoints |

The V22 checkpoints document a failed development candidate, while the V21
checkpoints document the historical release training path. This distinction is
useful for the decision, but it does not authorize choosing one set for the
owner.

Before another candidate is trained, the owner must choose one of these
explicit options:

1. archive selected snapshots outside the workspace and verify their hashes;
2. authorize deletion of exact superseded snapshot directories after preserving
   run, selection, prediction, and hash receipts; or
3. revise the storage budget and document why.

After the choice, rerun:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\measure_model_storage.py `
  --output artifacts\model-release\storage-audit-<date>.json
```

No new weights may be created while `within_budget` is false.
