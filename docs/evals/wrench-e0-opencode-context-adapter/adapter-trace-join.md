# Prepared-context adapter lifecycle-trace join evaluation

Job: `W2-NS-E0-ADAPTER-TRACE-JOIN-20260925`  
Nonce: `TRACE-ADAPT-B701`  
Base commit: `b74414e0cb542fa4d37637c9692591432e4f2869`  
Reviewer: `W2-NS-E0-ADAPTER-TRACE-JOIN-20260925-REVIEW`, nonce
`TRACE-ADAPT-B701-REV`

## Result

The focused integration test in
[`test_e0_lifecycle_accounting.py`](../../../tests/test_e0_lifecycle_accounting.py)
passes as part of **26 passed in 5.48 seconds** on the existing Python 3.11.16
and pytest 8.4.2 environment. The independent read-only review returned
**PASS** with no findings. The reviewer verified the test takes the event and
inserted message from `materialize_opencode_prepared_context`, projects the
before and after snapshots, and joins them through `build_partial_lifecycle_trace`
using the same READY preparation and finalized outcome. It does not read or
parse `PreparationResult.prompt`.

The READY envelope transition receipt SHA matches the adapter receipt and is
checked against preparation/session identity, the prompt-gate message digest
and position, and both projection digests. The other-session case returns no
adapter event and the trace builder returns `JOIN_MISMATCH` with no envelope.
The reviewer ran no tests and made no edits. `git diff --check` passed.

## Scope and limits

Only authored synthetic fixtures were used. This confirms that the already
implemented local materializer output can be structurally joined into the
current trace envelope and that a mismatched session is rejected. Inputs remain
caller-supplied and unauthenticated. No OpenCode hook or client ran; runtime
hook provenance, atomic capture, dispatch enforcement, final provider and
tokenizer parity, complete lifecycle accounting, and overall E0 acceptance
remain unverified.

The report is
[`adapter-trace-join.md`](../../reports/wrench-e0-opencode-context-adapter/adapter-trace-join.md).
The test file SHA-256 at freeze is
`46a577da1559fac7bdb5613694dbfaa3fdebb07c1cbe670949c4d4948ccd50c0`.
