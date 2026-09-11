# Trusted scenario data V1

This is the data gate for Wrench production-value and cloud-cost claims. It
does not create production data and it does not call a provider.

## Required input

Provide an operator-approved JSONL file. Every row must contain:

- `id`: stable unique scenario identifier
- `source_class`: `observed_production_replay`, `synthetic`, or `adversarial`
- `source_ref_sha256`: lowercase SHA-256 of the approved source reference
- `redaction`: an object whose `status` is `complete`
- `prompt`: the redacted public request
- `context`: the redacted public context object
- `replay_eligible`: `true` only when the row is approved for replay

Rows must not contain evaluator gold, expected answers, fixture objects,
credentials, private keys, bearer tokens, passwords, or unresolved raw user
content. Production-derived rows must remain distinguishable from generated
or adversarial rows.

## Price ledger

Provide a versioned JSON object containing `version`, `provider`, `model`,
`currency` set to `USD`, `effective_from`, `source`,
`input_price_per_million`, and `output_price_per_million`. Add
`cached_input_price_per_million` when the provider exposes a separate cached
input price. The source and effective date are mandatory so a later rerun can
reconstruct the cost assumption.

## Audit command

When the operator has an authorized trace export containing `prompt` and
`context`, first reduce it to the audit schema:

```powershell
py -3 -X utf8 scripts/redact_production_scenarios.py `
  --input <authorized-trace-export.jsonl> `
  --output <approved-redacted-scenarios.jsonl> `
  --authorization-receipt <authorization-receipt.json>
```

The reducer writes only the fields consumed by the audit, copies the source
hash to each row, deterministically replaces recognized credentials, and
rejects evaluator-only fields. `source_class` is mandatory and must be
explicitly one of `observed_production_replay`, `synthetic`, or `adversarial`;
there is no production default. The authorization receipt must contain
`{"authorized": true, "source_sha256": "..."}` matching the input export. It
does not call a provider.

The metadata-only source discovery also scans adjacent `.sqlite3` files in the
source directory. It records file hashes, table names, column names, and row
counts, but never records cell values. SQLite rows are not replay-eligible by
themselves; they still require an authorized prompt/context export and a
verified request-to-usage join.

```powershell
.venv\Scripts\python.exe -X utf8 scripts\trusted_scenario_audit.py `
  --input <approved-redacted-scenarios.jsonl> `
  --price-ledger <versioned-price-ledger.json> `
  --output artifacts\trusted-scenarios\<run-id>
```

For schema-only development without a production claim, add
`--allow-no-production`. A real production-value run must omit that flag and
must contain at least one `observed_production_replay` row. The audit writes a
manifest and an audit receipt and exits nonzero on rejection.

Before any M3 provider invocation, verify the paired readiness receipt:

```powershell
py -3 -X utf8 scripts/verify_trusted_readiness.py `
  --receipt artifacts/trusted-scenarios/<run-id>/receipt.json
```

The command must return `PASS`. A `REJECTED` result is a hard stop for M3,
regardless of whether local-only tests are green.

## Replay and measurement contract

Freeze the audit manifest and hashes before assigning rows to A/B/C. Use the
same scenario IDs, endpoint, model, executor, turn limit, and accounting in
each arm. Record prompt tokens, completion tokens, cached tokens, request and
retry counts, billed cost when reported, ledger-estimated cost, latency,
fallback, final outcome, and boundary status.

Report production-derived, synthetic, and adversarial strata separately. Also
report weighted results using an explicitly documented production sampling
weight and unweighted results. Never call a schema-only receipt production
evidence, and never mix estimated cost with provider-reported cost without
labeling both.

## Current repository state

No authorized production replay file is currently present in this workspace.
The existing authored selective campaign remains valid for local safety
testing but is not evidence of real-traffic prevalence or cloud savings.
