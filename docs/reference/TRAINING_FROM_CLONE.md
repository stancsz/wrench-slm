# Training and using the adapter from a clone

This guide describes the maintained V21 path. Run commands from the repository root. Creating a new adapter does not reproduce V21 quality automatically. No training or external gateway is started by setup.

## 1. Environment

The recorded release environment is Windows, Python 3.14 and CUDA on an RTX 5070 Ti. Git and ripgrep (`rg`) are needed by the disposable execution evaluator. Use an isolated Python environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements/dev.txt
python scripts/verify_assets.py
python -m pytest -q
```

On Unix, activate with `source .venv/bin/activate`. That makes the environment usable but does not establish Linux evaluation parity. CPU tests do not require CUDA; install a matching CPU PyTorch wheel when only reviewing data and code. Training and release_eval.py currently require CUDA.

## 2. Fetch the dependencies explicitly

The trainer and preflight default to offline cached loading. Populate the cache first:

```powershell
hf download Qwen/Qwen2.5-0.5B-Instruct --revision 7ae557604adf67be50417f59c2c2f167def9a775
```

For the full frozen V21 inference package or the V20 initializer, authenticate to the private asset repository:

```powershell
hf auth login
python scripts/fetch_assets.py --list
python scripts/fetch_assets.py --asset package-v21
python scripts/fetch_assets.py --asset package-v20
```

The catalog pins the remote revision and archive SHA-256. Extraction checks paths and refuses to overwrite differing local files. Packages restore to their original artifacts/model-release locations. The upstream base remains separate. The plain adapter repository on Hugging Face remains usable through PEFT, but these full packages additionally include the validated runtime and examples.

Historical source and training receipts can be fetched separately with `--asset training-evidence`, `--asset authored-history`, and `--asset original-source`. Most users need only the release package, or the initializer for V21 recipe reproduction.

## 3. Choose a dataset

The canonical V21 data is `data/releases/release-generalization-v21`. Its manifests and split bytes are frozen. V20 is retained for lineage. The context-release-v2b suite is evaluation-only despite its historical filename development.jsonl.

To check generator reproducibility without overwriting release files:

```powershell
python scripts/release_clean_v21_data.py --output artifacts/model-release/generated-check-v21
python scripts/release_context_v21_data.py --output artifacts/model-release/generated-check-context
```

Output directories must be new. Dataset JSONL hashes should match the frozen manifests; generator-source hashes can differ after maintenance. Original generator snapshots are preserved with the data and in the original-source bundle.

For your own adapter, prepare a new directory under artifacts/model-release with train.jsonl, development.jsonl, evaluation.jsonl and manifest.json in the same schema. Each row needs the public prompt/context and a target as illustrated by the release data, plus unique IDs and family/language labels. Freeze family-disjoint development and evaluation sets before training. Never use the published V21 evaluation suites to iteratively tune a candidate and then call them independent tests.

## 4. Audit before training

```powershell
python scripts/audit_training_data.py --data data/releases/release-generalization-v21 --split train --output artifacts/model-release/audit-my-train.json
python scripts/audit_training_data.py --data data/releases/release-generalization-v21 --split development --output artifacts/model-release/audit-my-development.json
python scripts/release_preflight.py --data data/releases/release-generalization-v21 --output artifacts/model-release/preflight-my-run
```

The semantic auditor checks the Wrench authored contract. Preflight verifies hashes, target validation, family/input separation, and token budgets. It expects a populated tokenizer cache. Different task schemas need corresponding validators and fixture implementations, not just replacement text rows.

## 5. Train a bounded candidate

This reproduces the V21 recipe using its V20 initializer, with a new output directory:

```powershell
python scripts/pilot_train.py --train data/releases/release-generalization-v21/train.jsonl --val data/releases/release-generalization-v21/development.jsonl --output artifacts/model-release/my-v21-run --steps 300 --max-length 1536 --batch-size 2 --accumulation 8 --learning-rate 2e-6 --seed 42 --checkpoint-every 100 --initialize-adapter artifacts/model-release/package-selected-v20/weights
```

To train a new adapter from the pinned base, omit --initialize-adapter and choose hyperparameters for your data. That is a different training run, not a reproduction of the V21 initializer lineage. Add --download-base to permit the trainer to fetch a missing base. It otherwise stays offline.

The trainer records source hashes, configuration, metrics and checkpoint state. Exact resume uses --resume-from with a trusted trainer_state.pt; do not combine it with --initialize-adapter. A warm start intentionally resets the optimizer. Hardware/library differences can prevent bit-identical results even with the same seed.

The 5 GB local model/checkpoint budget applies to new runs too. Do not run this alongside retained full runs without reviewing available space. Use the retention tools described in the release handoff; do not delete the only release or initializer copy.

## 6. Evaluate development and select

Evaluate every declared checkpoint on development, using a distinct output directory:

```powershell
python scripts/release_eval.py --data data/releases/release-generalization-v21 --split development --checkpoint artifacts/model-release/my-v21-run/step-000100 --output artifacts/model-release/my-dev100 --execute
python scripts/release_eval.py --data data/releases/release-generalization-v21 --split development --checkpoint artifacts/model-release/my-v21-run/step-000200 --output artifacts/model-release/my-dev200 --execute
python scripts/release_eval.py --data data/releases/release-generalization-v21 --split development --checkpoint artifacts/model-release/my-v21-run/checkpoint --output artifacts/model-release/my-dev300 --execute
python scripts/release_select.py --training-run artifacts/model-release/my-v21-run --evaluations artifacts/model-release/my-dev100 artifacts/model-release/my-dev200 artifacts/model-release/my-dev300 --output artifacts/model-release/my-selection
```

The selector requires all declared checkpoints. Inspect selection.json and use its selected checkpoint, rather than assuming step 200 will win again.

--execute uses disposable fixture tools, including read-only commands and a local health endpoint. It does not execute arbitrary requests from live users. The fixtures do not certify arbitrary shell safety.

## 7. Export and verify

Pass the selected path from selection.json to package_weights.py. The license input must be the pinned upstream Apache license; the restored V20/V21 package includes it.

```powershell
python scripts/package_weights.py --checkpoint PATH_FROM_SELECTION --output artifacts/model-release/my-package --license artifacts/model-release/package-selected-v20/LICENSE-QWEN
python scripts/release_eval.py --data data/releases/release-generalization-v21 --split evaluation --package artifacts/model-release/my-package --output artifacts/model-release/my-final-evaluation --execute
```

PATH_FROM_SELECTION is an explicit placeholder. Export produces an unapproved candidate. Complete an independent final evaluation and a fresh-environment package check before assigning release status. Consult `python scripts/verify_weight_package.py --help` for its explicit Python and local-base requirements.

For the restored V21 package, the runnable example is:

```powershell
python -B artifacts/model-release/package-selected-v21/inference.py --input artifacts/model-release/package-selected-v21/example.json --device cuda
```

Use -B because the frozen historical package includes checksummed bytecode. Normal imports can rewrite it after relocation and invalidate the manifest. The maintained evaluator and package verifier disable bytecode writes automatically.

It loads the pinned base and returns a proposal; it does not execute tools.

## Provenance and limits

Small release cards, receipts, hashes and input data are in Git under releases/v21 and data/releases. Large packages and historical assets are separate checksummed downloads. Raw logs and public-reference acquisitions are preserved locally, excluded from these release bundles, and not claimed as V21 training inputs.

Archived manifests may name old paths. releases/v21/path-map.json maps moved data to its current location. Frozen package bytes, including their checksum-covered runtime files, must not be edited to modernize paths. The original-source bundle preserves the pre-cleanup source checkout for historical reproduction.
