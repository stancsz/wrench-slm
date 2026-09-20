# Phase 190: v74 held-out final split diagnostic

Date: 2026-09-20

The case runner now has an explicit `--allow-noncanonical-count` switch for
named held-out splits. The default canonical 220-case guard remains unchanged.
The v2 `final.jsonl` contains 44 rows across seven task families, with 24
eligible, 12 boundary, and 8 out-of-domain cases. It was never used for
training, routing selection, or prompt tuning in this run.

## Receipt

The fresh v74 package ran the final split through its model-local endpoint with
the client mechanical shortcut disabled:

- `canonical_case_count`: `false`;
- outcome matches: `43/44`;
- eligible exact accepts: `23/24`;
- prohibited accepts: `0`;
- transport/runtime abstentions: `0`;
- model calls: `0`;
- raw input tokens: `4,733`;
- input tokens not sent to model: `4,733`;
- median latency: `23.267 ms`;
- p95 latency: `77.761 ms`.

The one eligible miss was a `localhost:4000/health` probe that returned
`health_read_error` because the live host service did not return the expected
bounded response. The proposal itself was correctly formed and the verifier
failed closed. This is held-out diagnostic evidence, not a final quality or
production pass.

