# Iteration 124: snapshot-bound deterministic mechanical route

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-SNAPSHOT-RULE-LOOKUP-ITER124`  
Status: **3/3 exact mechanical answers through Wrench's snapshot-bound rule route; 3/3 fail-closed controls passed**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Paired task results

This run replaces Iteration 122's direct in-memory read with Wrench's actual
`run_e0_rule_route` path. It wrote the frozen authored fixture under the
approved temporary root, bound the root, created one source snapshot, then
asked the rule route to read only the exact file named by each query. Standard
library TOML/AST parsing answered the question after the retrieved bytes were
verified. All three reads succeeded from the same snapshot and every required
source line was present.

| Case | Route action | Verified answer | Exact snapshot bytes read | Source evidence SHA-256 |
|---|---|---|---:|---|
| Retry policy | `read_file` | `3,250` | 307 | `2ae3e968de8956a2087132a0b2147cad558b44783c620ee199456828496ae588` |
| Session lifetime | `read_file` | `1800,300` | 307 | `2ae3e968de8956a2087132a0b2147cad558b44783c620ee199456828496ae588` |
| Retry function | `read_file` | `calculate_retry_delay` | 589 | `7485fbc3671617dd5d0bab363223fd3f7de358bde206739806686a994e91062a` |
| **Total** | **3 reads** | **3/3 pass** | **1,203** | **one frozen snapshot** |

The snapshot SHA-256 was
`2e8460e254168719d5c038653eed9b5985b8236c53519157e3b93139782056fd`.
Three additional controls passed: reading a path absent from the snapshot
abstained with `source_not_in_snapshot`; a code-mutation request abstained
with `ambiguous_or_unsupported_request`; and changing a source after snapshot
creation abstained with `snapshot_read_changed`.

This is direct evidence that Wrench can route this fixed mechanical slice
without invoking a language model. It is not a measured token-saving rate.
The receipt leaves `frontier_tokens_saved` null because no paired
frontier-only generation or provider usage was measured. The 1,203 bytes read
also are not directly comparable to the local-model arm's 1,392 input tokens:
the local arm includes E0 context preparation and model prompt construction,
while this arm returns exact file observations to a deterministic parser.

## Identity and admission

- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Runner SHA-256:
  `46825065c3198ed9b0b07d9eb30dd389a761a04ae4211365d5a9c47495c2d818`.
- Wrench route, mechanical parser, and snapshot source hashes are recorded in
  the receipt alongside the fixture and snapshot identities.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\snapshot-rule-lookup-iter124.json`,
  3,939 bytes, SHA-256
  `7b35268560245303431e484e65c7997bfee663294159e695d724820cee696935`.
- At admission, RAM was 19.86% free. Storage reserved 20,000,000 bytes,
  included the Docker WSL model volume and hourly automation directory, and
  stayed under the 50 GB aggregate limit. C: had over 140 GB free. The job
  exited, its temporary tree was confirmed absent, and no job process remained.
- No local model, GPU inference, download, provider call, or spend occurred.

The result remains a three-query synthetic diagnostic. It does not show
unseen-task coverage, code changes, test repair, model value on ambiguous
decisions, frontier-only success retention, full-lifecycle tokens, cost, or
all-day reliability. Keep all acceptance gates open. Next add this route arm
to a matched common episode harness with a real downstream baseline, then
measure where deterministic abstention invokes a local controller and whether
that controller improves verified outcomes.
