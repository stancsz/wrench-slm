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

## Follow-up: bind completed route evidence to preparation

Status: bounded trace-binding change verified and independently reviewed.

The partial trace now accepts a completed route only through a successful
`RoutePreparationResult`. It verifies the route-preparation accounting receipt
and requires its preparation to equal the preparation carried by the
OpenCode session join by object identity (both references must point to the
same in-memory result). The v3 envelope records the route-preparation receipt
digest. A standalone completed `RuleRouteResult` is rejected; a non-completed
route may still be represented as an abstention/unknown reference. The trace
continues to label all records caller supplied and untrusted.

This tightens cross-record consistency for route paths and content hashes. It
does not authenticate execution, prevent dispatch, establish user intent, or
close any runtime, tokenizer, accounting, outcome-truth, or utility gate.

Focused verification used Python 3.11.16 and the existing cached pytest
runtime: `tests/test_e0_lifecycle_accounting.py` passed **14 tests** in 2.92
seconds. The first run exposed a fixture snapshot mismatch in the new
same-snapshot path/content case; the fixture was corrected to use the same
two-file snapshot and the focused rerun passed. No packages were installed.
Pytest scratch remained under `C:\wrench-slm-data\tmp` and is included in the
storage inventory. The 10,000,000-byte reservation was released after the run;
the final storage status was `WITHIN_LIMIT` with 666,150,681 actual bytes and
103,000 bytes in other active reservations.

Independent read-only review passed with no blocking findings
(`W2-NS-E0-TRACE-ROUTEPREP-FINAL-REVIEW-20260925`, nonce
`TRPLINK-FINAL-REV-C91B`). It checked the source, tests, and docs but did not
run tests. The reviewed source and test SHA-256 values were respectively
`82895E4179EE039CB9F44542FE8A22F548E1D4061F9EE4FC7710B19D72C2E19B` and
`7DCC9E8730F0C24F8F017A88724AFAE6A08CD19B24E19A205EE8E5BB93984212`.

## Follow-up: bind transition to prepared context

The prompt-gate receipt now records the SHA-256 of the exact context message
and its insertion position when a nonempty READY context is produced. Both
fields are included in preparation aggregate schema
`wrench.e0-preparation-refs.v2`; failed, empty, and non-ready gates carry null
insertion identity. The lifecycle envelope is now
`wrench.e0.partial-lifecycle-trace.v4`.

The prepared-transition validator requires a READY preparation and prompt
gate, matches the expected message digest and position, validates the exact
insertion across bounded before/after projections, and emits a content-free
receipt linked to the preparation aggregate. Lifecycle accounting verifies
the receipt and binds its session and after-projection digest to the trace. A
trace containing route-preparation evidence now requires this transition.
Route-validation failures retain their existing error classification.

Focused verification on Windows Python 3.11.16 with the existing cached
pytest runtime passed **97 tests** across `test_prompt_compiler.py`,
`test_e0_context_pipeline.py`, `test_opencode_hook_projection.py`, and
`test_e0_lifecycle_accounting.py`. No packages were installed. The first run
found a context-message size-limit alias issue and three lifecycle fixtures
that had not supplied the now-required transition; those were corrected and
the complete focused rerun passed. The 10 MB focused-test reservation remains
active pending final output accounting; pytest scratch is under
`C:\wrench-slm-data\tmp\e0-prep-transition-tests-20260925\pytest`.

The first independent read-only review found a P2 receipt-verifier gap: it
accepted positions outside the hook message bound. The verifier now rejects
positions at or above `MAX_HOOK_MESSAGES`, and a regression rehashes an
otherwise valid receipt with an impossible position to verify rejection.
Targeted independent re-review is pending. `git diff --check` passed after the
code correction; source and test hashes are recorded in the evaluation.

## Limits

The validator accepts caller-supplied projections and expected message data.
It does not authenticate the OpenCode hook, validate every nested client
message or option schema, prove dispatch prevention, reconstruct the final
provider request, or establish tokenizer parity. The transition receipt is
local structural evidence only. Runtime installation/execution, provider
calls, real-task collection, customer utility, and overall E0 acceptance are
outside this slice.
