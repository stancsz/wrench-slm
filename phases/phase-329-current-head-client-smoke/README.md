# Phase 329: Current-head package route and client smoke

Status: `PASSED`, diagnostic integration evidence.

The exact portable package `D:\models\_wrench-release-candidate-85ff83c`,
materialized from source commit `85ff83c`, was exercised through its own
model-local endpoint and client templates.

## 4M model-local route

- Requested raw payload: `4,000,000` tokens.
- Raw payload: `35,199,491` characters.
- Package route elapsed time: `28.748 ms`.
- Model calls: `0`.
- Effective working context: `19` tokens for the exact lookup case.
- First-layer gate latency: `28.232 ms`.
- Raw payload hash was bound and the route returned a verified read proposal.

## Real client smoke

- OpenCode: exit `0`, structured read observed.
- DeepSeek Harness: exit `0`, structured read observed.
- Claude Code: exit `0`, read tool result observed through the Anthropic
  messages adapter.
- Wrench traces used the `embedded-mechanical` and
  `embedded-mechanical-settlement` backends.
- Model calls: `0`.
- Mutation claim: `false`.
- Claude first gate: `2.534 ms`.

Primary receipts:

- `../phase-329-current-head-package-4m-route.json`
- `receipt.json`
- `wrench-client.trace.jsonl`
- `claude.trace.jsonl`

## Boundary

This proves the current package identity, model-local raw 4M intake, and
read-only client wiring. It is not dense-native 4M attention quality, a learned
MiniMax parity claim, independent RTX 5060 Ti verification, or production
approval.
