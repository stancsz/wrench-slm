# Failing-test evidence packet screen 01 evaluation

Status: **INCONCLUSIVE; runner failed before producing a score**
Date: 2026-09-26
Review: independent static pre-run review passed; reviewer did not execute the screen.

## Evidence

The frozen protocol and fixture identities matched the files at launch. The
runner began the first positive case, performed the two snapshot-bound exact
read routes, parsed the failure records, and raised
`ValueError: packet_oracle_mismatch` at the packet comparison. Inspection of
the hash-bound runner and oracle shows why: the parser's finding dictionaries
contain `source_sha256` and `log_sha256`, but the expected packet omits these
receipt-only fields. Direct whole-dictionary equality always rejects that
shape. The other five cases were not reached.

This is a scorer implementation defect discovered by the one authorized
screen attempt. It must not be interpreted as a pass or failure rate for the
local work class. The frozen protocol explicitly prohibits rerunning or tuning
the exposed fixture, so no repair-and-rerun was performed.

## Limits and disposition

- Positive packet accuracy: **unavailable**.
- Correct boundary count: **unavailable**.
- Semantic SLM acceptance: not measured; this was a deterministic screen.
- Frontier-token savings: **N/A**, zero eligible matched pairs.
- No model, client, provider, network, training, or real task was used.

The result artifact is the runner-failure receipt linked in
[the task report](../../reports/wrench-local-acceptability/failing-test-evidence-packet-screen-01.md).
Future work needs a fresh fixture and separate protocol, a field-aware packet
comparison, and independent pre-run review. Keep training stopped pending a
screen that supplies valid task-quality evidence.
