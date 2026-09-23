# Phase 433: configured loopback baseline authorization

## Finding and change

The paired real-client canary previously exempted loopback baseline URLs from its external-baseline approval guard. `http://localhost:4000/v1` is loopback but can still dispatch paid provider requests. The canary now requires a child contract for every configured baseline URL, including loopback, and requires gateway accounting capture before it creates an output directory or makes a network request. The contract must bind the exact workload SHA-256, endpoint, model, one repetition, a finite positive USD maximum, and a provider hard-cap reference. The runner records the child contract hash in its receipt. It does not enforce or independently verify the provider cap. A human must verify the cap outside the runner.

The built-in deterministic stub remains the zero-spend path. The guard does not change the existing non-loopback HTTPS, key, and external-switch requirements.

## Verification and evidence

- Read-only `GET http://localhost:4000/v1/models` returned HTTP 200 and advertised `minimax-guided`. This is model inventory, not proof of dispatch, cost, or spend control.
- A read-only inspection of the local gateway config found `disable_spend_logs: true` and no provider hard-cap reference. No paid model request was sent in this phase.
- The focused canary tests reject a missing contract before an output directory is created, and reject mismatched bindings, zero, infinity, and `unlimited` spend values. The positive contract fixture is synthetic and not spending authorization.
- `python -m pytest -q tests/test_paired_client_canary.py`: 43 passed. `python -m pytest -q`: 293 passed, 18 deprecation warnings. Q4 contract validation returned `VALID`.
- The local deterministic three-client regression is in [local-stub-regression.json](local-stub-regression.json). It completed the direct and hybrid client paths, with zero hybrid model calls and clean process-tree cleanup. Its verdict is `INCONCLUSIVE_PAIRED_REAL_CLIENT_HYBRID_CANARY_ACCOUNTING_INCOMPLETE`; baseline frontier tokens and paid cost were not observed. This is not a Gate C or D pass.

## Q4 decision still open

The human first answered `unlimited spend`, then stated a `$500` ceiling for the proposed single canary. The latter supplies a finite maximum, but no provider-enforced hard-cap reference or provider cost export was supplied. The active parent Q4 contract still has `monetary_budget: 0`; it has not been amended by this phase. No paid call is authorized by these notes alone. Recommendation: keep the zero-spend boundary until a human-reviewed provider hard cap at or below the stated ceiling, an exact approved child contract, and a provider-authoritative cost export path are available. Alternative: explicitly revise the GOAL/Q4 spending rule, with its added uncapped-spend risk accepted by the product owner. Rollback for any future approved canary is to stop further requests and preserve request-level receipts. There is no deadline that changes this stop condition.
