# Mixed-lifecycle ledger bridge evaluation

Status: **pass for synthetic receipt conversion mechanics only**
Date: 2026-09-26
Implementation: [bridge report](../../reports/wrench-local-acceptability/mixed-lifecycle-ledger-bridge-20260926.md)

## Checks

The focused standard-library suite passed **7/7** cases:

- mixed local/frontier attempts, retry, fallback, tool and verifier calls
- unknown cost with exact tokens
- missing usage tainting the entire arm
- duplicate, unmatched, wrong-route and wrong-frontier-counter taint
- malformed comparison and duplicate task rejection
- oversized input and unhashable enum rejection
- reject a `not_run` local/frontier work-call route while preserving a `none/not_run` row

The additional regression closes a static-review finding: without it, a
`not_run` work-call with route `local` or `frontier` entered expected usage
coverage and was counted as an executed model call. Those rows now fail closed.

The synthetic fixture's exact arithmetic was baseline 31 frontier tokens,
Wrench 22, or 29.032258% reduction. This figure is only a bridge/reporter
plumbing check. The adapter downgraded both caller-supplied
`independently_verified` outcome claims to `user_reported`, so the reporter
returned zero successful pairs and no success-qualified average.

## Limits

This evaluation does not establish any local SLM task acceptability or
frontier-token savings. Inputs are caller supplied; no authenticated OpenCode
dispatch, provider usage, matched real task, independent outcome oracle, or
tokenizer parity was observed. The practical frontier-saving result remains
**N/A**, with zero actual eligible matched pairs. No inference, client,
provider, endpoint, or model call was made.
