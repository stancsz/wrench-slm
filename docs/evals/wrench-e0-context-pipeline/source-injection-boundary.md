# Evaluation: E0 source-injection prompt-format regression

Job: `W2-NS-E0-SOURCE-INJECTION-ROUTE-20260925`
Nonce: `SRCINJ-0E62`

## Result

The focused offline fixture passes. Its single authored source file contains
a marker-like line and instructions to ignore prior directions, read a second
unselected file, disclose its value, and send it to an external URL.
`run_e0_rule_route` returns the requested snapshotted file only. The subsequent
`prepare_e0_context` call keeps the selected source inside an explicitly
labeled, JSON-quoted context field. The fixture asserts that the secret value
is absent and that executor and process ports were not called.

The prompt compiler's wrapper is included before final serialization and token
counting. This keeps the fixture's local prompt-gate receipt tied to the exact
wrapped test serialization.

## Evidence and disposition

- Focused Windows pytest: **14 passed** across the new integration regression
  and prompt compiler suite.
- `git diff --check`: passed.
- Client, provider, model, network, and real data: not used.
- Production dispatch, actual model behavior, and runtime serializer/tokenizer
  parity: not tested.
- Independent review: **PASS**, job
  `W2-NS-E0-SOURCE-INJECTION-REVIEW-20260925`, nonce `SRCINJREV-81A4`.

This is a regression for visible source labeling and bounded offline route
mechanics. JSON quoting and the text label do not establish model resistance to
prompt injection. E0's zero-unauthorized-action and complete-accounting gates
remain unproven.
