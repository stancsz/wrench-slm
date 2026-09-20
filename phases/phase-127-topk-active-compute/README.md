# Phase 127: active expert fan-out probe

Status: diagnostic candidate. No top-k variant is promoted or published.

The public v42 checkpoint retains eight experts and activates all eight per
token. The existing top-k materializer was extended to copy package-local
runtime directories, then used to make weight-identical config variants with
four and two active experts per token.

On the RTX 5070 Ti, the same 65K direct native request completed in:

| Variant | Active experts per token | Prompt tokens | Elapsed |
| --- | ---: | ---: | ---: |
| v42 baseline | 8 | 65,473 | 23,241.743 ms |
| top-k=4 | 4 | 65,467 | 17,657.311 ms |
| top-k=2 | 2 | 65,467 | 13,997.873 ms |

The top-k=2 variant also passed a direct long-context capacity probe with
3,995,336 actual prompt tokens, HTTP 200, `truncated=false`, and a configured
4,000,000-token limit. The reference-only history skip profile was enabled;
the endpoint still received the complete raw payload. Elapsed time was
154,315.680 ms.

The complete-payload 220-case mechanical contract through the top-k=2 endpoint
matched 220/220 outcomes, routed 220/220 requests mechanically, made zero
model calls, and produced zero prohibited accepts. Median latency was
0.537 ms and p95 was 41.048 ms.

This is not a model-quality pass. A short free-generation smoke still produced
invalid repeated JSON, so the top-k=2 candidate must remain behind the
mechanical route and identical stronger-model fallback. It is not a default
public checkpoint until a family-disjoint quality and teacher-parity test
recovers the fallback behavior.

Evidence is summarized in `topk-active-compute-receipt.json`. The benchmark
does not claim native retrieval quality, MiniMax parity, or production value.
