# Phase 437: paid-cost cap and provider-model binding

Date: 2026-09-22

## Finding and change

The paid-cost validator reconciled the provider export to the reported charge,
but it did not compare that charge with the approved child contract's maximum.
A correctly reconciled provider charge could therefore be reported as bound
evidence even if it exceeded the authorized cap.

The validator now accepts only receipt schema v2 and requires the exact active
parent contract and approved child contract files. It hashes both files,
reuses the canary's v2 approval checks, and requires the receipt to carry those
same hashes plus the requested gateway endpoint and model alias. The shared
contract check binds the child approval to the current parent hash, workload,
endpoint, requested model, one repetition, and positive hard-cap reference. It
also enforces `child.max_spend_usd <= parent.monetary_budget`. The validator
rejects the receipt if the summed provider charge exceeds that approved child
cap.

The provider's HTTPS endpoint and reported model remain distinct from the
requested gateway endpoint and alias. Provider export records must still
match the provider endpoint receipt's model, request IDs, token usage, cost,
and currency. The child contract now binds `model` as the requested gateway
alias and `expected_provider_model` as the expected provider-reported identity.
The receipt's provider `model` must exactly match the latter, and every export
record must match the receipt. The MiniMax-specific model pin is removed, but
these checks do not independently prove that the gateway alias dispatches to
the approved provider identity.

## Verification

- Focused paid-cost validator tests: 16 passed, including distinct alias and
  provider identity checks, child/provider/export mismatches, legacy-schema
  rejection, over-cap rejection, parent/child hash mismatches, and zero-parent
  rejection.
- Paid-cost validator and paired-canary suites: 60 passed.
- Full repository suite: 324 passed with 18 existing Windows asyncio
  deprecation warnings.
- Ruff passed for the validator, tests, and paired-canary contract guard.
- Q4 contract validation returned `VALID`; the parent contract now records
  the approved `$500` ceiling for exactly one paid paired canary. The ceiling
  does not replace the required provider-enforced cap.
- The validator's CLI help includes the required child-contract input and
  defaults the parent-contract input to the active repository contract.
- The new [child-contract v2 template](child-contract-v2.template.json) binds
  the alias and expected provider model separately. Its `template: true` and
  `PENDING` status are rejected by preflight before output creation or gateway
  access and cannot authorize a run.
- The checker establishes consistency with the supplied parent, child, and
  export files. It does not prove provider-export authenticity or correlate
  provider request IDs to a particular client session; human source review is
  still required.
- Q4 contract validation returned `VALID` after recording the Q4 approval.
- All authorization fixtures use synthetic files. No provider request,
  credential access, or spend occurred.
- A fresh read-only `GET http://127.0.0.1:4000/v1/models` listed `current`,
  `openai`, `codex-subscription`, and other aliases, but no literal `gpt-6`
  alias or provider dispatch mapping. The human identified the current route
  as GPT-6; no completion request was made. Exact alias dispatch remains
  unverified.
- Read-only `GET /model_group/info` returned the requested aliases but no
  upstream model identity. `GET /v1/model/info` returned HTTP 400 for the
  checked aliases. Without credentials, `GET /provider/budgets` returned HTTP
  500 and `GET /management/v1/budgets` returned HTTP 403. No provider cap was
  verified; no credential was supplied or inspected.
- Sol's follow-up review recommended removing the MiniMax pin only with
  separate child-bound gateway-alias and expected provider-model fields, while
  keeping the canary stopped. The implementation followed that recommendation
  and added mismatch, missing-identity, and export-row regressions.
  Consultation usage: 519 prompt tokens, 271 completion tokens, 790 total;
  `decision_changed: true`. See
  [advisor packet](advisor-packet-gpt6-model-binding.txt).

Source identities:

- `COLLABORATION_CONTRACT.json`: SHA-256
  `b28649ac55b1eb328dc620296768badc69a2cc1f189dfaa377c3005f38f6cfba`
- `tools/validate_paid_cost_receipt.py`: SHA-256
  `d21d40ff37c8704ad8bd3b35b8b756bc6a913bb77622ea5fdaabfce55d367c88`
- `tests/test_validate_paid_cost_receipt.py`: SHA-256
  `f8989cfcbd9b73c2b5f9cc9a31ea632fcc2490010931fe6159d73639ea0b30d3`
- `tools/probe_paired_real_client_canary.py`: SHA-256
  `d22f7a19b40907d87aa9361109137ee521506227ef164f12614f4a4a102812b1`
- `tests/test_paired_client_canary.py`: SHA-256
  `321f2e665dc799e84d5a45ed62b446c9f827c3660c44bf65cf1df6ae42f9461b`
- `child-contract-v2.template.json`: SHA-256
  `b357f9d5f57f7907aefd4a57670b7c15e0671f15f18a0d40340a829d2818bc8b`
- `provider-receipt-v2.template.json`: SHA-256
  `a83040f578862de4545a72e3a951be5888de20283216e49d4a0d165bf28829d4`
- `advisor-packet-gpt6-model-binding.txt`: SHA-256
  `d2a1258b498732826dab57c46475da0e6a5c0c4d4be608a7a3925353bc66eee9`
- The active parent Q4 contract now allows at most `$500` for exactly one
  paired canary. No child contract has been issued, and the missing provider
  hard-cap reference still blocks execution.

The current receipt shape is
[provider-receipt-v2.template.json](provider-receipt-v2.template.json). The
provider export schema remains v1 and is unchanged. Phase 406's receipt
template is historical v1 and must not be used with the current validator.

## Q4 decision and execution gate

Q4 decision: the human approved exactly one paid paired canary for workload
SHA-256 `a7633846225827f0877a0e4202706be4f2c4c4a5118d6069c78755c4323729ce`,
one repetition, through `http://localhost:4000/v1` on the GPT-6 route, with a
maximum of `$500`. The
active parent contract now records that one-run ceiling. This approval does not
authorize any additional run, production routing, or spend above the cap. Keep
execution on hold until the exact gateway alias and provider dispatch are
verified, a provider-enforced cap within `$500` is confirmed, the
provider-authoritative cost-export retrieval path is verified, and a schema-v2
child contract binds the exact parent hash, workload, endpoint, requested
model alias, expected provider-model identity, repetition, and maximum spend.
Capture the actual provider export after the run. The
read-only model inventory did not identify a literal `gpt-6` alias. Do not
guess the mapping. Read-only budget endpoints did not verify a provider cap,
and no credentials were used to try admin access. Rollback remains limited to
the validator and tests;
preserve prior v1 artifacts as historical evidence. No production routing or
release authority changes are included.
