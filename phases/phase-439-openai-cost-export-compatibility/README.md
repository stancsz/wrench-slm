# Phase 439: OpenAI aggregate cost-export compatibility

Date: 2026-09-22

## Decision and scope

The user approved the Q4-recommended local implementation path. OpenAI's
organization Costs API reports daily aggregate totals, while the existing
Wrench `provider-cost-export.v1` contract required one provider-priced row per
request. The work adds a separate aggregate evidence schema and preserves the
request-row path. It does not access credentials, configure an OpenAI project,
make a provider request, or authorize spend beyond the existing one-canary
approval.

The active paid-canary child contract is now schema v3. It must bind its
accounting mode before the canary runner can start. Request-row accounting
requires a provider, HTTPS export endpoint, and reviewed retrieval reference.
OpenAI aggregate accounting additionally requires exact project and API-key
IDs, a one- or two-day UTC bucket interval, affirmative dedicated-project and
exclusive-key assertions, isolation evidence, current project spend, the
project hard limit, and a positive hard-limit overrun reserve. Preflight
requires:

```text
project_hard_limit_usd - current_project_spend_usd
    + hard_limit_overshoot_reserve_usd <= max_spend_usd
```

This is a fail-closed evidence check, not a guarantee that an unquantified
provider enforcement delay cannot exceed the human-supplied reserve. Source
and headroom evidence still require human review. OpenAI says hard limits can
return 429 responses after tracked spend reaches the limit, but enforcement is
not instantaneous and recorded spend can slightly exceed the configured
amount. A limit set at exactly `$500` is therefore not accepted as proof of a
strict `$500` maximum.

## Validator behavior

`wrench.openai-cost-export.aggregate.v1` mirrors the documented Costs API page
and bucket/result shape. The validator requires:

- The official Costs endpoint, a canonical hash for the included export, and a
  separate hash binding the complete evidence wrapper to the receipt.
- A single complete response page with `has_more: false` and `next_page: null`.
  Any pending pagination stops validation.
- Every daily bucket to match the child-bound UTC interval exactly, with no
  missing, duplicated, or out-of-order day.
- Every result to carry the exact child-bound project and API-key IDs, a valid
  nonnegative amount, and USD currency.
- The sum of all result amounts to reconcile to the paid receipt and to remain
  within the approved child maximum.
- Evidence assertions to match the human-approved child binding.

The official aggregate response does not provide per-request IDs, per-request
token counts, or provider model identity. Those remain in the Wrench/request
receipts and the separately verified route identity. The aggregate validator
does not invent them or imply request-level charge attribution. Project/key
exclusivity is human attested and must be supported by reviewed evidence. The
checker does not authenticate an API response or prove that the referenced
project settings were actually applied.

The prior schema-v2 child template is historical and no longer passes current
preflight. The new [schema-v3 child template](child-contract-v3.template.json)
and [OpenAI aggregate export template](openai-aggregate-cost-export.template.json)
are deliberately marked `template: true` and cannot authorize or validate a
real run.

## Live route and provider evidence

Read-only inspection found the listener on `127.0.0.1:4000` is the
`unified-llm-gateway` LiteLLM container. The running image was
`ghcr.io/berriai/litellm-database@sha256:bd07ceb1fc7c4505f116c4eb2767956a8accba3119548dd8ae55e5356a381d56`.
The mounted gateway configuration had SHA-256
`F2235AFD7F6F615EA58EFB52E7A92ED539523563171111001C2385A557C8EE4D`.

The mounted configuration maps alias `current` to `openai/current`, and
`codex-astra` to `openai/responses/gpt-6-astra`. Read-only model metadata now
identifies three explicit GPT-6 routes: `codex-subscription` to
`openai/responses/gpt-6-sol` (display `GPT-6 Sol`), `codex-astra` to
`openai/responses/gpt-6-astra` (display `GPT-6 Astra`), and `codex-luna` to
`openai/responses/gpt-6-luna` (display `GPT-6 Luna`). The `current` alias is
displayed only as `Current model` and maps to `openai/current`; the API does
not identify it as any of those GPT-6 variants. The user's GPT-6 clarification
does not identify which alias was intended. No completion was sent and no
provider-reported model is attached to a Wrench request. The exact GPT-6 alias
must be selected before binding the paid child.

The OpenAPI document confirms the read-only metadata query parameters. The
`/model/info?litellm_model_id=current` form returned HTTP 400. `/model/info`
succeeded when given the internal model-info ID, returning display name
`Current model`, provider `openai`, and configured model `openai/current`.
`/v2/model/info` exposed the explicit GPT-6 alias mappings above. A
metadata-inclusive `/models` query returned 19 entries but only generic
fallback metadata for `current`. Sanitized selected fields and statuses are preserved in the
[gateway route metadata receipt](gateway-route-metadata-2026-09-22.json). No
secrets or credentials were requested or displayed.

The official [OpenAI Costs API reference](https://developers.openai.com/api/reference/python/resources/admin/subresources/organization/subresources/usage/methods/costs)
documents `GET /v1/organization/costs`, daily buckets, project and API-key
filters, grouping by project, API key, and line item, and page continuation
fields. Authenticated access to this endpoint and an export for the approved
project remain unverified.

OpenAI's [spend-limits guide](https://developers.openai.com/api/docs/guides/spend-limits)
documents organization and project hard limits, 429 responses after tracked
spend reaches the limit, and possible slight overshoot because enforcement is
not instantaneous. No project hard limit, current project spend, overrun
reserve, or provider admin access was verified in this phase. No credentials
were read or supplied.

## Advisor review and Q4 disposition

An Astra advisor reviewed the incompatibility and recommended the isolated
aggregate path only conditionally: preserve request-level receipts, add a
versioned aggregate schema, bind project/key and full-bucket exclusivity, and
stop if attribution, provider-model identity, authenticated export access, or
the USD 500 bound cannot be established. It specifically cautioned that
delayed hard-limit enforcement alone does not establish the ceiling.

Consultation: request `chatcmpl-codex-advisor-f36c1e05922e`; 617 prompt tokens,
289 completion tokens, 906 total; `decision_changed: true`. The user approved
continuing this local validator and documentation path. The approval is not a
provider-call or credential approval.

A separate Sol review evaluated whether the human's GPT-6 route clarification
and the gateway's `current -> openai/current` mapping were sufficient to bind
the canary. Verdict: no. At that point the gateway had not exposed a GPT-6
identity for `current`.

Consultation: `codex-sol-advisor`, request
`chatcmpl-codex-advisor-ff5c036650c0`; 386 prompt tokens, 311 completion
tokens, 697 total, 1,220 packet characters; `decision_changed: true`. The
advice changed the next action from considering the human statement plus
registry mapping sufficient to requiring provider-side route identity evidence
before preparing the paid child. The advisor did not make a provider request.

Subsequent read-only `/v2/model/info` calls identified three configured GPT-6
choices: `codex-subscription` maps to `openai/responses/gpt-6-sol`,
`codex-astra` to `openai/responses/gpt-6-astra`, and `codex-luna` to
`openai/responses/gpt-6-luna`. This gateway metadata establishes each configured
alias-to-model mapping, not a completed provider dispatch. The user's GPT-6
clarification still does not identify which variant to bind. The next action is
human selection of the exact alias; `current` must not be treated as one of the
GPT-6 aliases. A typed Q4 `human.choose_option` request was submitted with
defer as the default and the three exact aliases as alternatives. No selection
has been received yet. Choosing an alias does not clear the spend, export, or
child-contract prerequisites.

## Verification and limits

- Before the implementation, a targeted local check of the documented OpenAI
  response failed the old validator with
  `provider_evidence_records_invalid`.
- Paid-cost validator and paired-canary tests: 66 passed.
- Ruff passed for the changed validator and canary preflight code/tests.
- Full repository regression: 339 passed, with 18 existing Windows asyncio
  deprecation warnings, in 60.92 seconds.
- Q4 contract validation returned `VALID`. `git diff --check` and
  `git diff --cached --check` passed. The final scope scan found no em dash
  characters in the edited files.
- A fresh focused rerun passed the same 66 paid-cost validator and paired-canary
  tests; Q4 contract validation again returned `VALID`.
- No gateway repository files were changed. Only read-only `GET` calls to the
  loopback gateway were made. No provider completion, credential access,
  account configuration, or paid spend occurred.
- Release remains not ready. Gates C and D remain open. Gate E remains open for
  serving lifecycle restart/recovery, complete accounting, no-mutation proof,
  and sustained operational evidence.

## Next decision and stop condition

The already approved one-run workload remains unchanged. The user's GPT-6
clarification does not specify which of the three registered GPT-6 aliases to
use. The next human decision is the exact alias to bind: `codex-subscription`,
`codex-astra`, or `codex-luna`. No answer means defer; do not substitute the
unresolved `current` alias. This choice alone does not clear the remaining
preflight. Before any provider request, the human must supply or verify a child
contract bound to the current parent hash, selected gateway alias and configured
upstream identity, workload hash, endpoint, one repetition, and no more than
`$500`.
For aggregate accounting this also
requires a dedicated OpenAI project and exclusive API key, complete day-bucket
coverage, authenticated Costs API access, current project spend, configured
project hard limit, a justified positive overrun reserve, and evidence that the
project's remaining hard-limit headroom plus that reserve fits inside the
approved ceiling. Read-only gateway metadata does not resolve `current` to
GPT-6. Obtain provider-side read-only route identity evidence and authenticated
cost-export evidence; never use a completion request as a diagnostic.

Stop if any alias or model identity is ambiguous, a billing bucket is incomplete,
project/key isolation is not independently supportable, the provider cap cannot
be bounded below the approved maximum, or the provider export cannot be
retrieved. Provide only redacted provider-side evidence, never raw credentials.
No account or project changes are authorized by the local implementation
approval. No provider request runs on the basis of the user's Q4 approval alone
while these prerequisites are absent.

Rollback is limited to the validator and its tests, the v3 child template, and
this phase's documentation. Preserve schema-v2 receipts and all prior phase
evidence as historical records. No source was committed.

## Source identities

The source hashes below record the Phase 439 implementation handoff. The later
route-metadata addendum changes documentation only and does not alter the
validator, canary preflight, or templates.

- `COLLABORATION_CONTRACT.json`: SHA-256
  `CF255E5C73AE9DF58C5FD29D879BD7AAA9A2972245EFB61A3C4C597F65D9B4B5`
- `GOAL.md`: SHA-256
  `689BA6BBFCF1DE6FECB156EDD9C44681FC3770E04C4C75439F27ED922F5D3B65`
- `tools/probe_paired_real_client_canary.py`: SHA-256
  `62851F07A559FFF3DE2FCFDC9B8C56878BC1D6DD7013821C081EAA1F1830F7D5`
- `tools/validate_paid_cost_receipt.py`: SHA-256
  `874CE89454EC7F1609F04832431A4752A26534EE553753A90141000305553F74`
- `tests/test_paired_client_canary.py`: SHA-256
  `A551DF009A7DB737A62977648EB9E742C0B194B73900CF9D15EA711B76C92415`
- `tests/test_validate_paid_cost_receipt.py`: SHA-256
  `49D26AC646D41FF7662BC57A07A4C04984C13B5050C5CC5F21BB10563A15C096`
- `child-contract-v3.template.json`: SHA-256
  `FEE4D452AA3E47EFE86961E1EDA9CAA2F0A554459BAD5CD2091E210451B04287`
- `openai-aggregate-cost-export.template.json`: SHA-256
  `E820E0170C5C48C8572FF1A90A2E0708DF7D38448FA2E255E225A0D605DD93C7`
- `advisor-packet-openai-aggregate-costs.txt`: SHA-256
  `766C422A3784DC5E97DEF95F91219BDBCEBA5CE2B0FE3C60062E18696241AB22`
- `gateway-route-metadata-2026-09-22.json`: SHA-256
  `F2B170B848150492E767D9E88AD17EB5635333C5A668B69979B1C648CBF283A6`
