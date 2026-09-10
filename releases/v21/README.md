# V21 release assets

This directory makes the release evidence available in a Git clone. The copied cards, manifest, training receipt, licenses and evidence are frozen snapshots of the original package. Their relative references describe that package's layout, not a new executable package here.

- files.json checksums the release datasets and small copied assets. Run python scripts/verify_assets.py.
- assets.json pins downloadable packages and historical archives by remote revision and SHA-256.
- path-map.json translates old data locations to the organized repository.
- evidence/ contains the release audits and evaluation receipts.
- release_manifest.json is the original full package manifest; it is not a manifest of this directory.

Use [Training from a clone](../../docs/reference/TRAINING_FROM_CLONE.md) for current commands.

## Included separately

The private asset repository holds the complete frozen V21 package, V20 initializer package, authored dataset history, training/evaluation source receipts, and original pre-cleanup source checkout. Fetch only what you need with scripts/fetch_assets.py. Weights are never added to this Git repository.

The base comes from the pinned upstream Qwen revision. Recoverable optimizer checkpoints remain local under the 5 GB model/checkpoint policy; the release bundles provide the initializer and training recipe, not all intermediate optimizer states.

## Preserved locally

Raw acquisitions, gateway traces, unpromoted builds and older baseline copies are retained under artifacts/archive/data. They were not used as the V21 authored training split and are not uploaded as release assets. Their names and locations are indexed in path-map.json. This avoids representing private logs or third-party reference data as redistributable adapter training data.

The data/archive/baseline directory in Git retains the previously published baseline and its dated receipts for existing legacy tests. Those results are distinct from the adapter evaluations.
