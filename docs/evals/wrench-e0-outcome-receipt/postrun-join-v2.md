# E0 post-run receipt join v2 evaluation

Goal: [bounded outcome receipt](../../goal/wrench-e0-outcome-receipt/GOAL.md)
Implementation: [post-run join report](../../reports/wrench-e0-outcome-receipt/postrun-join-v2.md)
Job: `W2-E0-POSTRUN-RECEIPT-JOIN-20260924`
Nonce: `POSTRUN-RECEIPT-83A1`
Baseline: `b3bf6193a4548bc003bea808a1045b08dc9451e4`

## Evaluation result

The local composition validates a ready preparation, its existing incomplete
v1 preparation receipt, the context aggregate digest, and the preparation
accounting receipt. It then creates a v2 reference-only receipt that links
caller-supplied post-task evidence independently from selected/omitted context
evidence. A sessionless v2 receipt is incomplete. Compact v2 identifier syntax
rejects arbitrary prose in task, run, session, verifier, and post-task evidence
ID fields.

## Verification evidence

- Six fixture functions in `tests/test_e0_request_record.py` passed when
  directly invoked using repository Python 3.11.16. They cover a successful
  join, evidence scope and namespace collisions, raw content and accounting
  tampering, session completeness, and opaque identifier syntax.
- The repository's `pytest` command was unavailable in the default Python
  3.13 runtime, the repository virtual environment, and the documented Python
  3.11 runtime. No packages were installed. No full test suite was run.
- `git diff --check` passed.
- Independent follow-up review on 2026-09-24 found no material findings.
  Review was read-only and did not execute tests.

## Limits

This is fixture-level contract evidence only. The join is in-memory and
caller-supplied; identifiers, evidence hashes, route, verifier claims, outcomes
and session identity are not authenticated. The syntax filter does not prove an
identifier contains no sensitive value. There is no client lifecycle capture,
runtime serializer/tokenizer equivalence, persistence/recovery qualification,
consented matched-task corpus, or authoritative success oracle. It is not E0
milestone acceptance, user-utility evidence, or permission to train or deploy.
