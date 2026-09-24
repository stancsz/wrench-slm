# E0 post-run outcome receipt join

Goal: [bounded outcome receipt](../../goal/wrench-e0-outcome-receipt/GOAL.md)
Job: `W2-E0-POSTRUN-RECEIPT-JOIN-20260924`
Nonce: `POSTRUN-RECEIPT-83A1`
Baseline: `b3bf6193a4548bc003bea808a1045b08dc9451e4`
Status: implementation complete; independent follow-up review found no material findings

## Change

Receipt v1 keeps its original selected-context evidence rules. Receipt v2 adds
an explicit session ID, the preparation-accounting receipt digest, and bounded
post-task evidence references containing only an ID, kind and SHA-256. In v2,
verifier and outcome references must point to those post-task references, whose
IDs cannot overlap selected or omitted context evidence.

V2 task, run, session, verifier, and post-task evidence IDs use a compact
opaque-ID syntax that excludes whitespace and arbitrary prose. A missing
session identity is required in `missing_fields`, yields an incomplete receipt,
and cannot be labeled complete. V1 ID and session behavior is unchanged.

`finalize_preparation_outcome` accepts only a ready preparation with a valid
incomplete preparation receipt and accounting companion. It copies the source,
context, selected and omitted evidence identities from that preparation and
binds its accounting digest before validating the caller-supplied post-run
record. It rejects a changed accounting receipt, a context item presented as
post-task evidence, duplicate namespace IDs, and raw content fields.

## Verification

- `git diff --check` passed for the current working tree.
- Six focused fixture functions were directly invoked with Python 3.11.16 and
  passed. Temporary source/store trees were created under
  `C:\wrench-slm-data` and removed when the harness exited.
- The focused `pytest` command could not run because `pytest` is absent from
  the default Python 3.13 runtime, the Python 3.11 runtime and the repository
  virtual environment. No package was installed.
- No full suite, OpenCode client, provider, model, persistence or external
  service was run.

## Limits and handoff

All post-run attempts, verifier identities, evidence hashes, session IDs and
outcome claims remain caller-supplied metadata. Hashes detect accidental
changes only; this code does not retrieve referenced artifacts, authenticate
the caller, establish verifier independence or consent, or prove task success.
The record is not persisted and does not establish full request-lifecycle
accounting. The OpenCode integration and runtime serializer/tokenizer remain
separate open E0 gates.

E0 remains open pending a pinned runtime/client integration, authenticated
lifecycle evidence, user authority, and a consented outcome corpus/oracle.
