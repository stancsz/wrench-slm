# Iteration 150: state-aware evidence in compact context

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-STATE-AWARE-CONTEXT-VERIFY-ITER150`  
Status: **state summaries preserve verified source lineage through typed compact serialization in the focused E0 test fixture**  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Work

The execution-state E0 fixture now exercises `compact_json_segments` as well
as the existing legacy format. The test builds a reviewed task-summary fact,
revalidates its source against the current snapshot, serializes the selected
segments under compact labels, then checks the label-to-segment order and the
summary's `summary_of` source lineage in the external receipt.

## Result

The combined focused suites passed **55 tests**:

```text
tests/test_execution_state_e0_context.py
tests/test_prompt_compiler.py
tests/test_e0_context_pipeline.py
55 passed in 5.17s
```

This verifies a narrow contract: an E0 summary derived from a current source
can keep its provenance after typed prompt serialization. It does not measure
token savings, model answer quality, multi-repository day-long engineering,
interruption recovery under power loss, or production readiness.

Test source SHA-256:
`C13404D75A3BE8E0CF84BB40F08E2848C6D735A45253D990E201EE52745DE4B1`.

## Next

Extend the answer-blind battery beyond the three lookups with stale source
handles, changed files, active diffs and interruptions. Measure how often
state-aware pruning preserves each required field and what recovery fetches
cost. Keep the candidate opt-in until the compact-format regression on 0.8B
is resolved or the model-size decision explicitly selects a compatible lead.
