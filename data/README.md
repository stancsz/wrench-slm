# Data catalog

The current adapter uses the authored datasets under `releases/`. Generated outputs, raw acquisitions, and historical experiments belong under ignored `artifacts/`, not alongside release inputs.

| Directory | Purpose | Training use |
| --- | --- | --- |
| `releases/release-generalization-v21/` | Frozen V21 train, development and evaluation splits | Train only on train.jsonl; select on development.jsonl |
| `releases/release-generalization-v20/` | Recorded V20 initializer dataset | Historical lineage |
| `releases/context-release-v2b/` | Post-freeze context suite; filename development.jsonl is historical | Evaluation only, never training |
| `archive/baseline/` | Earlier mixed-source corpus and legacy receipts | Not the V21 corpus |

V21 contains 6,144 training rows, 176 development rows and 440 evaluation rows. The context suite contains 220 rows. These are authored tasks and resettable fixtures, not production traffic.

Each release directory retains its original manifest and generator snapshot byte-for-byte. The copied generator.py is a provenance snapshot, not a standalone executable. Use the maintained scripts listed in [the training guide](../docs/reference/TRAINING_FROM_CLONE.md).

The historical datasets informed successive corrections; they must not be reused as independent release gates. Existing perfect evaluation results do not establish broad production quality.

## Integrity and storage

Run `python scripts/verify_assets.py` to check all catalogued release data and small release assets against SHA-256. Do not edit frozen files to make a failing check pass.

Historical authored experiments are preserved in `artifacts/archive/data/pilots/` and the downloadable authored-history asset bundle. Raw gateway logs, third-party acquisitions, and unpromoted builds remain local under `artifacts/archive/data/`. They are excluded from distribution because they are not V21 training inputs and may contain private or separately licensed material. Nothing was deleted during organization.

See [the release asset catalog](../releases/v21/README.md) for retrieval, original package locations, source snapshots, and the V20 dependency. Legacy manifests retain original paths as historical evidence.
