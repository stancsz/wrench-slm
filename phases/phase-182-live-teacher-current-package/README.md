# Phase 182: provider-backed teacher replay on current package

Date: 2026-09-20

## Scope

This replay reused the existing MiniMax cloud proposal capture from phase 128
and made no new provider calls. It ran the current v73-style downloaded Wrench
package through its model-local HTTP endpoint with the client mechanical fast
path disabled. The run is provider-backed diagnostic evidence, not a final
production claim, because the source capture is still the historical complete
patch contract and teacher proposals were not executed with mutation authority.

## Results

- 220 matched traces.
- 0 Wrench teacher fallbacks.
- Weighted Wrench final success: `93.1290%`.
- Weighted teacher final success: `60.5218%`.
- Weighted mechanical frontier-token coverage: `84.8103%`.
- Net frontier-token savings: `100%`.
- Wrench local model tokens: `23,961`.
- Teacher frontier tokens: `143,269` raw provider tokens, `63,383` in the
  weighted mechanical score denominator.
- Wrench median latency: `217.883 ms`.
- Wrench p95 latency: `387.115 ms`.
- Teacher median latency: `1,868.202 ms`.
- Teacher p95 latency: `7,886.598 ms`.
- Prohibited accepts: `0`.
- Unexpected mutations: `0`.

## Coverage gap

The 84.8103% coverage is not a reason to invent broader routing. The missing
eligible exact matches are concentrated in health-read prompts that say only
“bounded timeout” or “response cap”, while their expected target embeds
different concrete timeout and byte-limit values. Those values are not
mechanically recoverable from the prompt. Wrench correctly refuses to guess in
the cases where the package cannot prove the exact action.

The next real evaluation contract must state those bounds explicitly or move
such cases to a fallback-required category. This receipt therefore shows the
current package's provider-backed speed, safety, and frontier-token behavior,
but it does not close the final family-disjoint 90% coverage gate.

