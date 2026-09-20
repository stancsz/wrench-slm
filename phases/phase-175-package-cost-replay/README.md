# Phase 175: package-local cost replay

Date: 2026-09-20

## Evidence

The v73 package server was evaluated with the client mechanical fast path
disabled. This forces every request through the downloaded package, where the
embedded worker decides whether to spend model tokens.

- Prompt-complete contract: 220 cases.
- Outcome matches: 220/220.
- Exact eligible proposals: 120/120.
- Prohibited accepts: 0.
- Transport or runtime abstentions: 0.
- Package mechanical fast paths: 220/220.
- Model calls: 0.
- Cost receipts: 220/220.
- Raw input tokens: 23,409.
- Model prompt tokens: 0.
- Model completion tokens: 0.
- Local model tokens: 0.
- Input tokens not sent to a model: 23,409.
- Median end-to-end latency: 24.011 ms.
- p95 end-to-end latency: 81.938 ms.
- Total local elapsed reported by endpoint receipts: 947.935 ms.

## Interpretation

This is a package-local mechanical-worker result, not a MiniMax matched
workflow result. It shows the intended cost shape: the full raw request is
accepted by the model-local endpoint, deterministic reduction and verification
produce the typed action, and no model tokens are spent. Dollar cost remains
unpriced until an authorized hardware and provider price card is joined.

The replay runner was also corrected so that its accounting receipt is
initialized before the 220-case loop. The corrected runner was used for this
receipt.
