# Production evidence intake contract

Updated: 2026-09-11

This is the smallest input needed to run the production-value experiment. It
does not request raw logs in the repository. The export must be privacy-reviewed
and supplied only when the operator is authorized to use it for replay.

## Required replay package

Provide an input export and an authorization receipt with:

| Item | Required content |
| --- | --- |
| Source export | JSONL rows containing the public request and visible context needed by Wrench |
| Stable identity | Unique episode ID and stable request/trace join key |
| Tool context | Declared tool schema/resources visible to the agent at decision time |
| Outcome context | Real observation and final outcome fields needed to score completion |
| Provenance | `observed_production_replay`, `synthetic`, or `adversarial` per row |
| Authorization | `authorized: true`, `replay_eligible: true`, and exact SHA-256 of the source export |
| Privacy | Deterministic redaction of credentials, private keys, tokens, and identifying content |

The export must not contain evaluator-only gold fields, hidden expected
answers, or unredacted secrets. Synthetic and adversarial rows must remain
separate from observed production replay rows.

## Required cost and runtime ledger

Provide a versioned JSON ledger containing the provider/model identity and the
prices used for input, output, cached input, and any other billed unit. The
ledger must state its currency, effective date, billing granularity, and source.

The replay must define duration units and provide usable start/end or measured
duration fields. Mixed units and outliers must be rejected rather than silently
converted.

## Required operator ceilings

Before any provider call, supply explicit values for:

- maximum provider attempts;
- maximum total cloud tokens;
- maximum output tokens per request;
- fixed endpoint and model identity;
- explicit operator authorization for the paid run.

The canonical launch path is:

```powershell
py -3 -X utf8 scripts/run_authorized_selective_pilot.py `
  --trusted-readiness-receipt <passing-receipt.json> `
  -- `
  --data data/pilots/selective-offload-real-runtime-v2 `
  --split evaluation `
  --package artifacts/model-release/package-selected-v21 `
  --base-path artifacts/model-release/base-dependency-v1 `
  --output artifacts/selective-offload-real-runtime-v2/m3-authorized `
  --max-attempts <approved-attempt-ceiling> `
  --max-cloud-tokens <approved-token-ceiling> `
  --authorize-paid-run
```

The wrapper must first pass `scripts/verify_trusted_readiness.py`. If it
rejects, no provider process is started and no token-saving claim is possible.

## Acceptance output

The resulting A/B/C receipt must report, per episode and in aggregate:

- provider prompt, completion, cached, and billed tokens when available;
- calls, retries, fallbacks, local time, cloud time, and total latency;
- corrections, failures, final outcomes, and fixture-boundary status;
- family-paired uncertainty for token deltas and final outcomes;
- comparison of cloud-only, rules-plus-fallback, and learned-plus-fallback.

The learned path is enabled only if it saves frontier tokens after all
verification and corrections, does not worsen final outcomes, and produces no
local safety violation. Otherwise the documented result is rules-only or
disabled.
