# Phase 117: explicit patch route and public package regression

This phase hardens the bounded review-only patch route and verifies the
published package runtime after the change.

## Receipts

- `explicit-patch-route-receipt.json`
  - 20 explicit requests across replace, append, prepend, insert, and remove;
  - 20/20 accepted by the verifier;
  - 20/20 workspaces unchanged;
  - zero model calls;
  - approximately 46 ms total on the local probe.
- `portable-package-v31-validation.json`
  - structural package pass;
  - two Safetensors shards;
  - `config_max_position_embeddings=4000000`.
- `public-package-4m-route-v31.json`
  - 4,000,000-token mechanical payload route pass;
  - approximately 9.7 ms;
  - zero model calls.
- `full-220-embedded-v31.json`
  - 220/220 requests entered the embedded mechanical route;
  - 200/220 historical outcome matches;
  - 82/120 exact eligible proposals;
  - zero prohibited accepts;
  - zero transport/runtime abstentions;
  - median 0.257 ms and p95 51.659 ms.

The 20 historical mismatches are the accepted patch rows whose prompts name a
file but do not specify a change. Wrench returns `patch_content_missing`
instead of inventing a diff. They remain visible as an oracle-quality gap and
are not silently removed from the historical result. The separate explicit
patch probe is the aligned evidence for bounded patch work.

The public Hub runtime update was published in commit
`fc224840abf4cca194a68c691bfe42f6fb38cad1`.

These receipts prove deterministic package behavior and authority bounds, not
MiniMax parity, native dense 4M retrieval quality, or production readiness.
