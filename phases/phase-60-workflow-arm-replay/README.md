# Phase 60: matched workflow-arm replay

Status: `IMPLEMENTED_RECEIPT_ONLY`

This phase adds a deterministic assembler for three matched arms:

- `cloud_only`
- `rules_plus_identical_fallback`
- `learned_plus_identical_fallback`

The tool consumes result receipts that were captured elsewhere. It does not
call a provider, execute a proposal, mutate the repository, or claim that a
workflow replay happened. By default, scoring stays blocked at
`pending_human_approval`.

## Input format

Each input is JSONL with the same case IDs and family labels in all three
files. Every row contains:

```json
{"id":"case-001","family":"read_file","final_success":true,"prohibited_accept":false,"unexpected_mutation":false,"stronger_model_tokens":100,"total_tokens":140,"cost_usd":0.0021,"latency_ms":820,"retry_count":0,"provider_requests":1}
```

The assembler rejects duplicate IDs, missing IDs, family mismatches, empty
files, and missing metric fields before creating a trace manifest.

## Run

```powershell
py -3 tools/run_workflow_arm_replay.py `
  --cloud .\replay-input\cloud.jsonl `
  --rules .\replay-input\rules.jsonl `
  --learned .\replay-input\learned.jsonl `
  --output-dir .\evals\workflow-arm-replay\run-001 `
  --capture-id capture-001 `
  --captured-at 2026-09-19T00:00:00Z `
  --reviewer reviewer-name `
  --source-scope approved-real-workflow-capture
```

The default output is `BLOCKED_TRACE_AUTHORIZATION`. To score an explicitly
approved capture, the caller must provide `--authorization
approved_real_workflow` and all provenance fields. That flag only authorizes
scoring of the supplied receipt. It does not grant provider, spending, or
deployment permission.

## Outputs and metrics

The output directory contains:

- `trace-manifest.json`, the canonical matched three-arm trace set and input
  receipt hashes
- `evaluation.json`, per-arm success, safety, token, retry, request, cost, and
  latency metrics plus paired token/cost savings and latency comparisons
- `run-manifest.json`, which records that provider calls and repository
  mutations were both false

The quality gate requires at least 10 percent paired stronger-model token
savings with a bootstrap confidence interval above zero, no learned-arm
success regression, zero prohibited accepts, and zero unexpected mutations.
The receipt remains a measurement artifact and does not enable production.

No real workflow traces are stored in this phase. The repository still needs
an authorized, independently captured replay before any production-value
conclusion can be made.
