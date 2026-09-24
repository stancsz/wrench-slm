# Snapshot-bound deterministic rule-route evaluation

Job: `W2-NS-E0-ROUTE-IMPL-20260924`  
Nonce: `RTE-9A33`  
Implementation baseline: `1aca758ac298985c4e8f0fad055566c874a2418a`

## Scope reviewed

This is an offline code-and-test review of the bounded W4 read-route
component in `src/wrench_harness/e0_rule_route.py` and its focused fixtures in
`tests/test_e0_rule_route.py`. No model, provider, OpenCode client, external
process, or network request was run.

## Evidence

The focused suite ran on Windows with Python 3.11.16 and pytest 8.3.5:

```text
tests/test_e0_rule_route.py: 31 passed
```

`git diff --check` passed. Coverage includes exact file and line reads, search
scoped to snapshot members, partial results on the match cap, positive bounded
search wording, negative/contradictory/output-limited or unauthorized reads,
stale sources and replaced roots, malformed snapshots, source/file/byte/line
caps, unsupported actions, and executor/process tripwires.

## Independent review

An independent read-only reviewer inspected the final source, fixtures, and
this evaluation. The reviewer confirmed the bounded manifest validation,
carried root binding, route limits, and lack of a live executor/provider path.
The review also found and caused repairs for:

- Negated or contradictory requests that could otherwise expose snapshot text.
- Caller-constructed manifests that could be traversed before validation.
- Curly apostrophe denials (`Don’t read`).
- Over-broad handling of the word `no`, which rejected the valid bound phrase
  `no more than`.
- Over-broad handling of `not`, which rejected a normal `not found` search.
- Authorization terms inside quoted search literals, which rejected a search
  for the literal `permission`.
- Output-like phrases inside quoted search literals, which could be mistaken
  for response-shaping instructions after switching to quote-aware checks.
- Quoted output restrictions, which initially lost their value during intent
  normalization and could permit an answer-only request to return source text.

After those repairs, the focused suite passed with 31 tests. The independent
read-only reviewer returned **PASS** on the final route and test implementation.
The review confirms quote-aware denial/output checks, bound exact retrieval,
validated snapshot manifests, hard route limits, and no live executor,
provider, or process path. This evaluation records that disposition after the
review; the evaluator did not review this final disposition sentence itself.

## Limits

The implementation is a route component, not E0 acceptance. It does not join
to `PreparationResult`, finalize the existing outcome receipt, establish
complete baseline/request accounting, prove caller intent, authenticate a
session, or prevent a later client model dispatch. Search covers only the
finite supplied snapshot set and explicitly reports that scope. These fixtures
are authored mechanics checks, not customer-utility evidence.
