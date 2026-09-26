# Failing-test evidence packet screen 01

Goal: [Measure acceptable local work](../../goal/wrench-local-acceptability/GOAL.md)
Worker: root orchestrator
Status: **aborted before scoring; no result**
Date: 2026-09-26

## Attempt and outcome

Attempted one frozen, provider-free deterministic screen over three fresh
synthetic multi-failure logs and three missing, stale, or ambiguous boundaries.
The runner reached the first positive case's packet comparison, then exited
with `ValueError: packet_oracle_mismatch`. No aggregate score or boundary
results were produced. The runner itself adds `source_sha256` and `log_sha256`
to parsed findings, while the frozen expected packet contains only seven
task/evidence fields; whole-dictionary equality therefore fails before the
screen can score the expected fields.

The pre-run static reviewer passed the fixture and protocol, including all
file hashes, failure lines, source definitions, and boundary identities. That
review did not run the runner. The execution failure is a harness defect, not
a task-class result. The receipt records this attempt and the pre-run storage
and host observations at
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\failing-test-evidence-packet-screen-01.json`.

## Frozen inputs and bounds

- Protocol:
  [screen 01 protocol](../../evals/wrench-local-acceptability/failing-test-evidence-packet-screen-01-protocol.md)
- Fixture SHA-256: `914618905adcf48bc6d609f20b2588e61ae2b677d66b4e0f26eda05e62a3c898`
- Runner SHA-256 at execution: `e17194e2d498acc265ec80ee0dc908836cc8b4ff9f82c3611d5348a0236f7630`
- Repository HEAD: `1add6ea25066ffcd1a35d182ddd14ecaa4fce995`
- Command: `python -B tools/run_failing_test_evidence_packet_screen_01.py --output C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\failing-test-evidence-packet-screen-01.json`
- The process exited with code 1 after two exact read routes on the first
  positive case. The other five cases were not run.
- No model inference, training, client, provider, network, or real-data capture
  occurred.

## Decision

This screen is **inconclusive**. Keep its fixture exposed and do not rerun or
tune it. Training remains stopped. Existing measured local scope is still
limited to synthetic deterministic operation/draft mechanics; zero semantic
SLM task classes are accepted. Real-work utility is unmeasured and actual
frontier-token savings remains N/A with zero eligible matched pairs.

A future screen needs a new fixture, a corrected packet/oracle comparison, a
new frozen protocol, and independent review before execution. Do not promote
this failed attempt into a local-work acceptance result.
