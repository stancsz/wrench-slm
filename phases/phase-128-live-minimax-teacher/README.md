# Phase 128: provider-backed MiniMax teacher replay

This phase connects the 220-case diagnostic replay to the real MiniMax M3
OpenAI-compatible endpoint. The capture is proposal-only. It never executes a
proposal and never grants the teacher mutation authority.

## Provider capture

- Endpoint: `https://api.minimax.io/v1/chat/completions`
- Model id: `MiniMax-M3`
- Authentication: supplied through `MINIMAX_API_KEY`; the key is not stored
- Canonical input: `evals/wrench-expanded-v1/cases.jsonl`, 220 cases
- Canonical input SHA256: `54D06DFF69C2A330FBBA5ED13BA22817C287CB7EC384A59458EB4F5E291BB45A`
- Complete-patch input SHA256: `D127003E81EE57A32ADD86B68056CD5393408488356C86C1ED23D65066B1FB95`
- Both captures: 220/220 transport successes, no execution

The capture parser preserves MiniMax's raw `<think>` content and extracts the
final schema-bearing JSON object separately. The canonical capture had 188
complete normalized proposals and 150,421 provider total tokens. The
complete-patch capture had 187 complete normalized proposals and 143,269
provider total tokens.

## Canonical 220 replay

`replay-220-v5/evaluation.json` is the current canonical diagnostic replay:

- Wrench plus identical MiniMax fallback: 0 prohibited accepts, 0 mutations
- Weighted teacher final success: 55.17%
- Weighted Wrench final success: 61.44%
- Eligible mechanical token-mass coverage: 50.91%
- Net frontier-token savings: 59.67%
- Wrench fallback count: 140/220
- Teacher median/p95 latency: 2,434/8,526 ms
- Wrench plus fallback median/p95 latency: 2,502/8,678 ms

This does not pass the 90% mechanical coverage or 95% savings gates. The
historical canonical fixture contains under-specified patch prompts, so the
mechanical router correctly abstains instead of inventing a diff.

## Complete-payload diagnostic replay

`replay-complete-220-v2/evaluation.json` uses the complete-patch derivative
fixture. It is diagnostic only, not a final release split:

- 120 eligible cases all reached the local mechanical route
- Frontier-token savings: 100%
- Strict weighted exact-oracle coverage: 85.47%
- 0 prohibited accepts, 0 mutations, teacher non-inferiority passed

The remaining coverage gap is the fixture's 20 health cases. Their prompts
omit timeout and response-limit values while their expected target objects
contain varying values, so an exact proposal cannot be inferred mechanically
from the request. This is recorded as an evaluation-contract defect, not
silently converted into a pass.

The next required evidence is a family-disjoint real-workflow set with explicit
health bounds and complete patch content. These receipts are not MiniMax parity
or production-readiness claims.
