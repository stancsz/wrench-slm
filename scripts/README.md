# Script entry points

Run commands from the repository root. Install dependencies from requirements/ first. These are direct Python scripts; no editable package installation is required.

## Maintained adapter workflow

| Script | Role |
| --- | --- |
| verify_assets.py | Offline SHA-256 checks for tracked release inputs and evidence |
| fetch_assets.py | Download, verify and restore versioned full packages or historical assets |
| release_clean_v21_data.py --output PATH | Rebuild the authored V21 dataset in a new artifacts/ directory |
| release_context_v21_data.py --output PATH | Rebuild the evaluation-only context suite |
| audit_training_data.py | Semantic checks without training |
| release_preflight.py | Token budgets, schema, split identity and overlap checks |
| pilot_train.py | Bounded CUDA LoRA run; --download-base permits fetching the pinned base |
| release_eval.py | Evaluate base, checkpoint, or full package |
| release_select.py | Select checkpoints using development results |
| package_weights.py | Export an unapproved candidate with runtime and license |
| verify_weight_package.py | Verify package checksums, clean loading and predictions |
| training_exposure.py | Audit sample exposure during a declared run |
| prune_model_artifacts.py | Inspect/maintain the model storage budget |
| audit_usefulness_v2_data.py | Preflight V2 public inputs, family isolation and executable gold labels |
| rules_eval_v2.py | Evaluate the deterministic V2 public-context helper |
| pilot_power_v2.py | Reproduce the family-level uncertainty and simultaneous-comparison assessment |
| measure_model_storage.py | Measure the explicit retained model and checkpoint paths against the budget |
| build_usefulness_stress_v2.py | Build the separate out-of-contract stress population |
| stress_eval_v2.py | Evaluate packaged boundary behavior without executing returned actions |
| benchmark_package_runtime.py | Measure bounded packaged cold, warm, memory, throughput, and queue behavior |
| audit_usefulness_v2_lineage.py | Audit retained ancestor source coverage and exact or heuristic overlap limits |
| pilot_run.py | Run the explicit V2 three-arm workflow; requires the V21 package, V2 data and fixed endpoint |
| pilot_analyze_v2.py | Analyze a complete V2 workflow with family-level uncertainty |
| selective_local_eval.py | Run the selective local gate on all assigned requests; supports `--bypass` |
| analyze_selective_offload.py | Summarize selective receipts with family-clustered bootstrap intervals |
| selective_pilot_run.py | Run the frozen selective A/B/C workflow; requires an explicit token ceiling and `--authorize-paid-run` |
| analyze_selective_workflow.py | Analyze complete selective A/B/C receipts, accounting, paired quality, and token tradeoffs |

See [Training from a clone](../docs/reference/TRAINING_FROM_CLONE.md) for the supported sequence. Package creation does not approve or publish a release.

## Historical generators and experiments

Other versioned release_* generators are retained because newer versions import earlier definitions and because their source documents the training lineage. Their archived input datasets can be restored with fetch_assets.py. They are not independent release gates for V21.

pilot_analyze.py implements the historical V1 local/cloud analysis and keeps its old denominators for receipt compatibility. The maintained V2 runner and analyzer require explicit V2 data, package, endpoint and budget inputs. They require an external provider for workflow phases and are not part of the adapter-only workflow.

The acquisition, ingestion, enrichment, transpilation and legacy verification scripts are historical tools. They are not required for V21 reproduction. Legacy mutation tools use artifacts/legacy-work/data; copy baseline inputs there explicitly before using them. They may overwrite that scratch dataset. Historical gateway inputs belong in artifacts/legacy-work/gateway-logs. fetch_real_data.py writes under artifacts/acquisition.

verify_milestones.py evaluates the old baseline and writes artifacts/legacy-reports. Its M3 result is not the V21 evaluation. The legacy Docker sidecar is isolated under examples/legacy-sidecar and is not a V21 serving recipe.
