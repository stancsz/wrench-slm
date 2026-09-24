# E0 rule-route partial trace join

Job: `W2-NS-E0-ROUTE-RECEIPT-20260924`  
Nonce: `RTE-8C61`  
Baseline: `45162350068eaf6541e15b1eec5dca995b1c0559`

## Change

`RuleRouteResult` carries the digest of the caller-supplied source snapshot
used by `run_e0_rule_route`. The partial lifecycle trace accepts an optional
route result and emits a versioned v2 envelope only when its digest matches
the preparation/outcome snapshot. The summary contains the route status,
action, bounded reason, hashed path references, content hashes, and counters
copied from the result with `caller_reported` field names. It omits raw paths
and the observation payload entirely. Actions, reasons, and evidence statuses
are allowlisted; unknown caller strings become the fixed value `other`. Invalid
shapes, unbounded values, and mismatched snapshot digests are rejected.

The synthetic end-to-end fixture calls `prepare_opencode_e0_context` for a
local authored source, reruns the bounded route over an equal snapshot,
projects a synthetic context-hook event, finalizes a caller-supplied outcome
receipt, then joins the route result to the trace. It also covers a real route
abstention and a route result from a different snapshot.

## Verification

Windows Python 3.11.16 with cached pytest 9.1.1 ran
`tests/test_e0_lifecycle_accounting.py` and `tests/test_e0_rule_route.py` after
the caller-string sanitization: **41 passed**. `git diff --check` passed. The
test base directory is under
`C:\wrench-slm-data\tmp\W2-NS-E0-ROUTE-RECEIPT-20260924\pytest`. The storage
checker reported `WITHIN_LIMIT` before the final focused run with 10,067,577,169
actual bytes, 40,103,000 reserved bytes, and 39,892,319,830 bytes projected
headroom. After the run it reported `WITHIN_LIMIT` with 10,067,598,784 actual
bytes, 40,103,000 reserved bytes, and 39,892,298,215 bytes projected
headroom. The 10,000,000-byte job reservation was released after independent
review. The subsequent status was `WITHIN_LIMIT` with 10,067,603,139 actual
bytes, 30,103,000 reserved bytes, and 39,902,293,860 bytes projected
headroom. The reservation included
the pre-existing shared uv cache (9,379,396,658 bytes) because the cached
Python 3.11.16/pytest runtime used for this run resides there. Test scratch was
kept under the approved Wrench data root.

The first independent review found that arbitrary caller-controlled strings
could enter the summary. Raw paths are now hashed and unknown action, reason,
and evidence-status values map to `other`. A second independent review is
PASS (`W2-NS-E0-ROUTE-RECEIPT-FINAL-REVIEW2-20260924`, nonce
`RTE-REV2-6B90`); it found no remaining scoped blockers and did not run tests.

## Limits

The route result and its snapshot digest remain caller-supplied and
unauthenticated. A caller can construct or modify a result. The summary is a
structural reference; it does not establish that the route ran, validate user
intent, authorize or prevent client dispatch, prove downstream task truth, or
measure runtime/provider activity or customer utility. No source observations
are copied into the envelope. The lifecycle envelope remains partial E0
evidence.

See the [evaluation](../../evals/wrench-e0-context-pipeline/route-trace-join.md)
and [goal](../../goal/wrench-e0-context-pipeline/GOAL.md).
