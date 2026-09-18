# Phase 41: request-intent verifier guard

The Phase 40 family-disjoint holdout found that a model could rewrite a regex
search request as an accepted literal search by omitting `mode`. The adapter
now carries the latest user prompt into the independent verifier. When the
request explicitly mentions a regex and the model proposes a literal search,
the verifier returns the existing `literal_mode_required` fallback reason.

This is a narrow fail-closed control. It does not infer arbitrary intent,
execute a regex, or authorize new actions. The original request remains
available to the caller for escalation.

The updated local test suite passes 17 tests. A rerun of the same 14-case
holdout reached 7/14 accepted cases, 12/14 expected outcomes, and zero
prohibited accepts. The full runtime receipt is
`../phase-40-few-shot-adapter/runtime-16e-adaptive-holdout-v2.json`.
The previous 8/14, 11/14, one-prohibited-accept result remains in
`runtime-16e-adaptive-holdout.json` for an explicit before/after comparison.

This is verifier and synthetic-holdout evidence only. It does not establish
real-workflow value, token savings, or production readiness.
