# E0 outcome receipt opaque-reference follow-up

Job: `W2-NS-RECEIPT-V3-20260924`
Nonce: `RECEIPT-V3-3C81`
Baseline: `bc96277225f0870f99dde8921ae836c01a6be43d`

## Change

New finalizations use `wrench.e0.outcome-receipt.v3`. V3 applies the existing
compact ASCII identifier syntax to all identity and reference values,
including context and post-task evidence IDs, retrieval misses, attempts and
retry links, work calls, verifier/outcome evidence, corrections, and token
counters. Existing v1 and v2 validators retain their prior acceptance rules.
The v1 preparation receipt is validated as before; if its copied references
cannot satisfy v3, the finalizer returns an invalid receipt rather than
rewriting or obscuring those references. The OpenCode finalizer also requires
the joined snapshot digest to match the snapshot bound in the completed
receipt.

This is a syntax boundary only. Compact IDs and hashes can still be sensitive
or linkable, and syntax does not establish reference provenance, existence,
consent, redaction, or truth. The finalizer still consumes caller-supplied
post-run metadata and does not observe or authenticate client activity.

## Verification

- Thirteen direct v3 negative fixtures rejected prose/path-like values across
  the reference classes changed by this contract.
- V1 and v2 compatibility matrices accepted legacy printable task/run,
  evidence, attempt/retry, work-call, usage-counter, accounting-counter, and
  correction references wherever those schema versions allow them.
- Eight existing receipt checks and six finalizer/OpenCode fixtures passed by
  direct function invocation, including session and snapshot mismatch cases.
- `git diff --check` passed. The focused fixtures were invoked from Python with
  a minimal pytest decorator stub because pytest is unavailable.
- `python -m pytest tests/test_outcome_receipt.py tests/test_e0_request_record.py
  -q` could not run because pytest is not installed. No dependencies were
  installed.

## Limits and remaining gates

This receipt improvement does not complete E0. The OpenCode serializer and
tokenizer match, client dispatch authority, full lifecycle/resource
accounting, runtime session identity format, consented matched-task corpus,
and outcome oracle remain unresolved. No client, provider, model, or external
corpus was used.
