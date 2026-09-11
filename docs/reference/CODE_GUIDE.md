# Code and workflow guide

Updated: 2026-09-11

This guide explains how the Python code fits together. It is an index and
boundary document, not a promise that every experimental module is maintained
or enabled by the V21 package.

## Execution lifecycles

### Adapter release lifecycle

```text
data/release generator
        |
        v
preflight and semantic audit
        |
        v
LoRA training and checkpoint selection
        |
        v
package, checksum, clean-load verification
        |
        v
independent evaluation and release cards
```

The maintained entry points are described in
[`TRAINING_FROM_CLONE.md`](TRAINING_FROM_CLONE.md) and
[`MODEL_RELEASE_HANDOFF.md`](MODEL_RELEASE_HANDOFF.md). The selected V21
artifact is a LoRA adapter, so loading requires the pinned base model and the
runtime formatting/validation code.

### Selective-offload lifecycle

```text
public task record
        |
        v
rules or model proposal
        |
        v
public-action policy
        |
        +---- fallback on uncertainty
        v
bounded read-only fixture/tool observation
        |
        v
runtime observation verifier
        |
        +---- local result or fallback
        v
post-route offline scoring and episode accounting
```

The active contract is
[`goals/active/selective-offload-real-runtime-v2/GOAL.md`](../../goals/active/selective-offload-real-runtime-v2/GOAL.md).
The protocol and result documents define what is evidence and what remains
blocked.

## `wrench/` modules

| Module | Role | Status or boundary |
| --- | --- | --- |
| `protocol.py` | Parse, validate, canonicalize, and compare structured calls | Core data contract |
| `dataset.py` | Build prompts, completions, iterable datasets, and SFT batches | Core training data path |
| `release_data.py` | Generate versioned release rows | Maintained release lineage |
| `release_eval.py` | Score release outcomes and quality gates | Maintained release evaluation |
| `pilot_tasks.py` | Original pilot task construction | Historical compatibility |
| `pilot_tasks_v2.py` | V2 family-isolated public task construction | Maintained V2 pilot input |
| `pilot_tasks_v22.py` | V22 repair-candidate task construction | Experimental repair lineage |
| `selective_tasks.py` | Selective-offload task construction | Active experiment input |
| `policy.py` | Baseline predictions and prediction loading | Core baseline |
| `public_helper.py` | Deterministic public-context helper | Rules baseline for selective work |
| `selective_policy.py` | Public action eligibility and formatting | Active safety boundary |
| `selective_runtime.py` | Runtime action and observation verification | Active oracle-free boundary |
| `selective_eval.py` | Evaluate local routes and summarize selective receipts | Active experiment evaluator |
| `pilot_inference.py` | Run a Transformers/PEFT model on pilot records | V21 package-facing inference |
| `pilot_environment.py` | Disposable fixture environment and tool receipts | Test/evaluation infrastructure only |
| `pilot_workflow.py` | Bounded cloud/local episode execution and accounting | Provider run requires explicit authorization |
| `evaluate.py` | Baseline record evaluation and summaries | General evaluation utility |
| `inference.py` | Native local executor and benchmarks | Experimental native path |
| `weight_inference.py` | Load and verify packaged adapter runtime | Release package path |
| `model.py` | Native NanoWrench model components | Experimental, not V21 adapter weights |
| `tokenizer.py` | Native tokenizer implementation | Experimental native path |
| `fsm.py` | Character-level JSON/tool-call FSMs | Experimental validation/constrained-decoding support |
| `tokenizer_fsm.py` | Tokenizer grammar and token masks | Not proof of enabled V21 constrained decoding |
| `sft.py` | Native supervised fine-tuning loop | Training utility |
| `training.py` | LoRA and experimental GRPO routines | Experimental training utility |
| `pure_training.py` | From-scratch native model training and reload | Experimental research path |
| `reward.py` | Reward decomposition and command safety checks | Experimental training/evaluation support |
| `canary.py` | Legacy local/cloud canary simulation | Historical simulation, not live timing evidence |
| `sidecar.py` | Legacy gateway-log watcher and background trainer | Historical integration, not V21 serving |

## Script families

### Release and asset management

Use `fetch_assets.py` and `verify_assets.py` for the reproducible asset
catalog. Use `release_*_data.py`, `release_preflight.py`, `audit_training_data.py`,
`release_eval.py`, `release_select.py`, `package_weights.py`,
`verify_weight_package.py`, and `training_exposure.py` only with the release
handoff's declared paths and receipts. Older versioned generators preserve
lineage and are not independent V21 release gates.

### Selective and usefulness experiments

| Family | Entry points | Purpose |
| --- | --- | --- |
| V2 usefulness | `audit_usefulness_v2_data.py`, `rules_eval_v2.py`, `pilot_run.py`, `pilot_analyze_v2.py`, `pilot_power_v2.py` | Frozen three-arm pilot and uncertainty analysis |
| Stress and lineage | `build_usefulness_stress_v2.py`, `stress_eval_v2.py`, `audit_usefulness_v2_lineage.py` | Boundary and ancestor-data audits |
| Selective runtime | `selective_freeze_policy.py`, `selective_local_eval.py`, `analyze_selective_offload.py` | Freeze and evaluate local routing |
| Selective provider pilot | `selective_pilot_run.py`, `analyze_selective_workflow.py`, `selective_replay_variant.py` | Matched A/B/C workflow, only after prerequisites and authorization |

The selective provider runner must not be treated as a source of production
value merely because it can run. Its current readiness prerequisite is
independently checked by `verify_trusted_readiness.py`.

### Trusted scenario intake

The production-data evidence path is deliberately split into read-only stages:

1. `discover_production_sources.py` inventories sources without reading message
   bodies.
2. `profile_production_usage.py` measures available usage fields and duration
   coverage.
3. `redact_production_scenarios.py` converts an explicitly authorized source
   snapshot into deterministic redacted rows.
4. `trusted_scenario_audit.py` checks provenance, hashes, separation, and
   replay eligibility.
5. `build_production_readiness_receipt.py` records paired discovery/profile
   observations.
6. `verify_trusted_readiness.py` independently gates whether replay prerequisites
   are complete.

The current metadata-only receipt is expected to fail this gate when prompt or
context fields, a price ledger, or trustworthy duration units are absent.

### Historical data and runtime tools

`acquire_and_prepare_data.py`, `fetch_real_data.py`, `ingest_logs.py`,
`enrich_mechanical_tools.py`, `cross_platform_transpile.py`, `verify_milestones.py`,
and the legacy pruning/sidecar scripts are retained for historical workflows.
They write to artifact or legacy-work paths only when an operator explicitly
chooses that workflow. They are not required for the V21 clone workflow.

## Test families

| Tests | What they establish |
| --- | --- |
| `test_protocol.py`, `test_policy.py`, `test_grammar.py` | Structured-call and policy primitives |
| `test_release.py`, `test_release_context.py`, `test_release_boundaries.py` | Release data, context, and claim boundaries |
| `test_weight_package_verifier.py`, `test_asset_restore.py` | Package and asset integrity |
| `test_pilot_*.py`, `test_evaluate.py` | Pilot construction, inference, workflow, and scoring |
| `test_selective_offload.py`, `test_usefulness_v2_boundaries.py` | Oracle-free routing and experimental boundaries |
| `test_discover_production_sources.py`, `test_profile_production_usage.py`, `test_redact_production_scenarios.py` | Read-only trusted-scenario intake |
| `test_trusted_scenario_audit.py`, `test_build_production_readiness_receipt.py`, `test_verify_trusted_readiness.py` | Provenance and independent readiness gating |
| `test_native_model.py`, `test_sft.py`, `test_reward.py`, `test_training_data_audit.py`, `test_training_exposure.py` | Experimental training and audit utilities |

## Extension rules

- Add a new task shape only with a visible public record, explicit policy
  contract, runtime verifier, fallback tests, and a separate evaluation split.
- Do not use expected answers or hidden fixture labels in runtime routing.
- Keep authored, synthetic, adversarial, and production-derived data in
  separate paths and provenance strata.
- Add a receipt before adding a claim to public status pages or release cards.
- If a change alters product intent or a durable safety invariant, update the
  product spec or architecture before changing the active goal.
- Treat any new benchmark as scoped to its exact hardware, package, data, and
  command. Do not generalize it to hosted production behavior.
