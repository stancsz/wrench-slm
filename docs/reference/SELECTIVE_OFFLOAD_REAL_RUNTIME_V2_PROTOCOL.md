# Selective offload real-runtime V2 protocol

Updated: 2026-09-10

This protocol replaces the prior selective-offload receipts as the active
runtime-boundary experiment. The prior receipts remain historical diagnostic
evidence because their local route used an offline answer oracle.

## Contract

The local route may complete only one operation shape: a visible, explicitly
requested `read_file` action, either a bounded positive line range or a JSON
configuration read whose public request asks for the `region` field. The route
must use only public prompt/context, declared tools, policy, the proposed
action, the real observation, and the runtime boundary fingerprint.

The runtime verifier must not import or read `score_answer`, `env.task`,
`expected_answer`, fixture gold, task-kind labels, or offline scores. Offline
gold scoring occurs only after the route decision and is reported separately.
Commands, drafts, ambiguous requests, unsupported requests, invalid ranges,
missing tools, and over-budget requests fall back without local execution.

## Frozen identity

- Candidate: `artifacts/model-release/package-selected-v21`
- Package manifest SHA-256:
  `219d6e85cbadf4701796e6d27d49ed057d3fb182fbda5fbecc9be1f59c9e3ea7`
- Adapter SHA-256:
  `6a43d8cf1da19770fc4764e148c758c1b8022fca31a21db9bd80b40bb4be6348`
- Base revision: `7ae557604adf67be50417f59c2c2f167def9a775`
- Policy source: `wrench/selective_policy.py`
- Runtime verifier: `wrench/selective_runtime.py`
- Runtime token limits: 1,536 input tokens and 192 generated tokens
- Development split SHA-256:
  `c53e03f9ad57d244467e3d614388103d67b815485e3c2bf308b1074227cff02b`
- Evaluation split SHA-256:
  `0cda2e8873c775709ecb525def952052eeec7a54e4b1a7d760bad3f6bee64041`
- Campaign: `selective-offload-real-runtime-v2`

The selector choice is `eligible`, revision `intent-v2`, with the runtime
verifier narrowing actual local completion to the selected `read_file` shape.
The development receipt and source hashes must be captured in
`artifacts/selective-offload-real-runtime-v2/selection-eligible-v2.json` before
the evaluation split is run.

## Data isolation

The generator is `wrench/selective_tasks.py`. It creates 24 development
families and 120 evaluation families, five instances per family, 12 kinds, and
English and Chinese cases. Development and evaluation family IDs are disjoint.
Public inference receives only `prompt` and `context`; fixture, expected answer,
tool, args, and kind are private evaluator fields.

Build the campaign with:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\build_selective_offload_v1.py `
  --campaign selective-offload-real-runtime-v2 `
  --output data\pilots\selective-offload-real-runtime-v2
```

## M1 verification

Run the targeted oracle-free tests:

```powershell
pytest -q tests/test_selective_offload.py
```

The suite must include a gold-free environment, zero-cloud local completion,
operator bypass, invalid and irrelevant proposals, timeout, tool failure,
malformed or insufficient observations, verifier failure, and boundary
mutation. A mechanical source check must fail if the runtime route imports or
references the offline scorer or private task data.

## Development, freeze, and fresh evaluation

Run the development split with the immutable package:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\selective_local_eval.py `
  --data data\pilots\selective-offload-real-runtime-v2 `
  --split development `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --variant eligible `
  --revision intent-v2 `
  --output artifacts\selective-offload-real-runtime-v2\development-eligible
```

Freeze only if the development receipt has nonempty local completion, zero
offline-correctness errors among returned local results, zero prohibited local
actions, zero unexpected mutation, and complete rows. The freeze command is:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\selective_freeze_policy.py `
  --summary artifacts\selective-offload-real-runtime-v2\development-eligible\summary.json `
  --protocol docs\reference\SELECTIVE_OFFLOAD_REAL_RUNTIME_V2_PROTOCOL.md `
  --data data\pilots\selective-offload-real-runtime-v2 `
  --policy eligible `
  --revision intent-v2 `
  --runtime wrench\selective_runtime.py `
  --package artifacts\model-release\package-selected-v21 `
  --output artifacts\selective-offload-real-runtime-v2\selection-eligible.json
```

Only after the freeze receipt exists may the 600-task evaluation be run. The
evaluation must record runtime route and verifier results separately from
post-route offline scoring:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\selective_local_eval.py `
  --data data\pilots\selective-offload-real-runtime-v2 `
  --split evaluation `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --variant eligible `
  --revision intent-v2 `
  --output artifacts\selective-offload-real-runtime-v2\evaluation-eligible
```

## A/B/C workflow

Only after the fresh local gate passes may the provider workflow run. The
dedicated runner verifies the freeze receipt and requires an explicit token
ceiling and `--authorize-paid-run`:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\selective_pilot_run.py `
  --data data\pilots\selective-offload-real-runtime-v2 `
  --package artifacts\model-release\package-selected-v21 `
  --base-path artifacts\model-release\base-dependency-v1 `
  --output artifacts\selective-offload-real-runtime-v2\abc-<run-id> `
  --max-attempts <approved-attempt-ceiling> `
  --max-cloud-tokens <approved-token-ceiling> `
  --authorize-paid-run
```

Arm A is cloud-only. Arm B uses the deterministic helper plus the identical
runtime completion and fallback path. Arm C uses the local V21 proposal plus
that identical path. All arms use the same task list, endpoint, model, tool
executor, outcome checker, turn limit, token admission, and receipt checks.

Analyze a completed run with:

```powershell
.venv\Scripts\python.exe -X utf8 scripts\analyze_selective_workflow.py `
  --run artifacts\selective-offload-real-runtime-v2\abc-<run-id> `
  --local-quality-summary artifacts\selective-offload-real-runtime-v2\evaluation-eligible\summary.json
```

Report prompt, completion, cached, and billed tokens when present; calls,
corrections, fallbacks, failures, local load/inference/policy/execution/
formatting time, total latency, final outcomes, and family-paired uncertainty.

## Decision

- `MEASURED SELECTIVE BENEFIT` only if C improves on B with complete accounting,
  no local-caused wrong result or boundary violation, and no worse final
  outcomes against the matched baselines.
- `RULES-ONLY VALUE` if B adds value but C does not improve on B.
- `NO MEASURED BENEFIT` if neither path adds measured value.
- `LOCAL CAPABILITY ONLY` if the fresh local gate passes but the provider run
  cannot be authorized or completed.

None of these decisions authorizes production deployment. Authored fixtures are
not real-traffic frequency estimates.
