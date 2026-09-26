# Local context integration screen 01

Date: 2026-09-26  
Disposition: **inadmissible diagnostic; no accepted work class**

## Result

The retained synthetic receipt records the expected branch in all five cases:
one required-source positive reached E0 prompt readiness, and missing, stale,
ambiguous-path, and over-budget cases failed closed. The fixed runner reports
zero model/provider calls. Its positive case contains 720 characters by a
fixture character-count proxy; this is not a tokenizer or client token count.

This is **not an admitted acceptance screen**. The protocol requires the
orchestrator to retain a separate admission decision before invocation. No such
record was retained, and the protocol explicitly says the status remains `NO
RUN` without it. The runner was invoked anyway. Treat these case outcomes as a
one-time diagnostic only; do not use them to claim acceptance or to tune a
future fixture. The fixture is exposed and must not be rerun.

## Independent review and limits

Independent review passed the receipt against the pinned runner, fixture,
protocol, and committed pipeline identities, and confirmed the marker and five
recorded outcomes agree. Review also found these audit limits:

- The receipt omits `snapshot_sha256`, so a reader cannot independently
  reconstruct the positive evidence ID from the retained receipt. The pinned
  runner checked it during execution.
- No separate admission/reservation record was retained. This prevents a
  protocol-valid result regardless of the recorded case outcomes.
- The fixture is synthetic and exposed. There is no semantic answer, verified
  task outcome, downstream client request, or matched frontier attempt.

Run identities:

- Commit: `0d55f9769b38744d95fae768261763bdb3bac232`, immediate child of the
  pinned base `5a0d67f5f5bc94d8e0c5886bf0ba41b1e87150a3`.
- Protocol SHA-256: `78e345213581023036c3c50ebcdcf114f555a5d6c0664912b9fa312f9645c684`.
- Runner SHA-256: `0f0d9f3c00599d3dfeff9f844f92c980c97c4b7b072ef9f9cdabd99bfc360838`.
- Fixture SHA-256: `8f47a7d58473cf9db9778df6a43f06c0e753e166981a7b5909457242e1ab4949`.
- Pipeline SHA-256: `0646c7b2ab2a2575e75e9eb5a94dde1146498d1f6b0da911fd4783f7f7a5e549`.
- Receipt SHA-256: `cd97d6388d9eb4fca4a730636769849df5e48ed6aa19d856b7dad8e7b6bdca81`.

No model, tokenizer, OpenCode client, provider, or network call ran. The
diagnostic contributes no local SLM acceptance evidence and no frontier-token
savings pair. Training remains stopped.

## Next measurement gate

For deterministic E0 mechanics, prepare a fresh fixture and retain a machine-
readable orchestrator admission record before a one-shot invocation. Include
the snapshot hash in the retained receipt so an independent reviewer can
recompute evidence IDs. For local semantic work, first freeze a single narrow
task class, an independent outcome oracle, and an exact local model/runtime
identity; no such class is currently accepted. Frontier-token savings remain
N/A until matched exact usage and independently verified success evidence
exists in both local and frontier arms.

See the [frozen protocol](../../evals/wrench-local-acceptability/local-context-integration-screen-01-protocol.md)
and [evaluation](../../evals/wrench-local-acceptability/local-context-integration-screen-01-result.md).
