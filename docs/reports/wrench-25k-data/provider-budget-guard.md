# Provider and Spend Admission Guard Handoff

**Job:** W25K-GUARD-20260924-A  
**Nonce:** W25K-GB-44D0  
**Repository base:** `87909b958ac252b0b3b2cc720a300babb26b733d`

## Status

Implemented a local fail-closed admission guard and offline mocked-transport tests. No credential was read, no network request was made, and no inference was authorized. The unresolved prior 401 charge still blocks admission because the caller must provide an explicit reconciled charge status and matching remaining-cap amount.

## Files changed

- `tools/provider_budget_guard.py`: validates the approved human JSON, task-hashed child receipt, case-file hash, endpoint/model/provider pin, token/request bounds, immutable maximum rates, spend reservation, reconciliation, and output location.
- `tools/capture_minimax_teacher_traces.py`: runs admission before secret lookup or POST, enforces one worker and one case, adds OpenRouter provider routing restrictions and price limits, checks a conservative UTF-8 input-size ceiling and reported token usage, and stores only the normalized proposal, response model, provider usage/cost accounting, and response content hash.
- `tests/test_provider_budget_guard.py`: offline checks for admission, mutation rejection, full-reserve debit on missing usage, unknown-charge rejection before mocked POST, and provider-pinned payload/retention behavior.
- This report.

## Child receipt contract

The separate JSON receipt uses schema `wrench.provider-budget-child-receipt.v1`. Its `task_hash` is SHA-256 over canonical compact, key-sorted JSON for every receipt field except `task_hash` itself. It binds `approval_sha256`, exact `cases_canonical_sha256`, endpoint, model, provider, `allow_fallbacks: false`, workers, request count, input/output token ceilings, immutable maximum input/output rates per million tokens, source reference, local `source_path` and SHA-256, exact output path, maximum request reserve, and cumulative reserve. The input case hash normalizes line endings to LF, matching the repository's canonical JSONL hash behavior. Admission reads the local pricing JSON under `C:\wrench-slm-data`, verifies its byte hash and parsed model/input/output values against the child receipt, and checks that the CLI output path resolves to the receipt's exact output path.

The guard computes the minimum reserve implied by token ceilings and rates, rejects under-reservation, checks the caller's explicit prior spend plus remaining cap equals the approved USD 100 cap, and rejects any reserve above the remaining cap. A missing or invalid cost usage receipt debits the full admitted per-request reserve. Prior charge status must be `RECONCILED_CHARGED` or `RECONCILED_NOT_CHARGED`; `UNKNOWN` rejects before any POST.

## Routing and retained data

The request body pins `provider.only` to `minimax`, sets `allow_fallbacks` false, `enforce_distillable_text` true, `data_collection` to `deny`, and provider `max_price` directly to the child receipt's USD-per-million-token values, as specified by the supplied OpenRouter guidance. The one case must explicitly include `"synthetic": true`. The route contract follows the [OpenRouter provider selection documentation](https://openrouter.ai/docs/guides/routing/provider-selection); output-rights review remains subject to the [OpenRouter Terms](https://openrouter.ai/terms).

The CLI defaults `--auth-env` to `OPENROUTER_API_KEY`, requires a nonempty variable name and configured value before dispatch, and never writes or logs the credential value. After all local admission and case checks, an exclusive claim file is created next to the receipt's bound output path. This makes the one-case child receipt single-use for that output path and rejects a second attempt before POST; no retry is performed.

Only the normalized structured proposal, response model identifier, provider usage and cost accounting, and response content hash are written to the final capture artifact. Raw response text, prompts, identifiers, and reasoning are not written. A response model mismatch or token-ceiling breach removes the proposal from the retained normalized result.

## Verification

Command: `python -m unittest tests.test_provider_budget_guard -v`  
Result: 7 tests passed. `python -m py_compile tools/provider_budget_guard.py tools/capture_minimax_teacher_traces.py` also passed. Tests reject mutated pricing evidence and a mismatched output path. Transport checks use a mocked `urlopen`, including proof that unknown prior charge and missing authentication cause zero POST calls; no live provider was contacted.

## Assumptions and limitations

- The child receipt's rate source/hash must be supplied and reviewed by the owner. The guard proves the local file matches its bound hash and values but cannot validate that the external source is authoritative.
- The caller's reconciliation reference is an asserted owner input. The guard cannot independently access billing records, so unresolved charge status remains blocked.
- The byte-based input bound is intentionally conservative and tokenizer-free. Provider token usage is checked after the attempted call; exceeding a ceiling prevents proposal acceptance and incurs at least the full request reserve if usage is absent.
- Spend admission is for one request and one worker. The exclusive output-path claim prevents replay of this exact receipt/output pair; it is not a general account-wide budget lock across different approvals or outputs.
- Provider selection and request fields are guarded locally, but a mocked test does not establish actual upstream provider behavior or contractual data rights.

## Blockers and next action

No hash-bound child receipt with reviewed immutable rates and reconciled prior-charge evidence has been admitted here. The root orchestrator should independently inspect this diff, prepare the single synthetic case and child receipt, and keep dispatch disabled until the prior 401 charge is reconciled. This worker's changes are a proposal for independent review, not release acceptance.
