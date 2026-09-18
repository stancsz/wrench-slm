# Phase 36: unseen schema-guided adapter comparison

This phase runs the same 28-case explicit-schema fixture through the strict
`execute_local_qwen` adapter for both packed tiers. Each request uses the exact
system prompt from the calibration rows, a localhost FreeToken endpoint, and
the repository verifier. The model server was started and stopped separately
for each tier.

Results:

- 8E, 3.188 GiB: 10/28 responses were accepted by the adapter. The 20 task
  cases yielded 8/20 accepted; 6/8 boundary cases abstained and 2 were
  prohibited accepts.
- 16E, 3.718 GiB: 10/28 responses were accepted by the adapter. The 20 task
  cases yielded 8/20 accepted; 7/8 boundary cases abstained and 1 was a
  prohibited accept.

The 16E tier matched 16/28 expected accept or abstain outcomes, while 8E
matched 14/28. These are independent runtime receipts, not a production
quality claim. The prohibited accepts keep both tiers non-promotable until a
new safety-focused calibration and matched real-workflow evaluation are done.

Receipts:

- `runtime-8e.json`
- `runtime-16e.json`

