# E0 bounded outcome receipt report

Job: `W2-E0-OUTCOME-RECEIPT-20260924`  
Nonce: `OREC-a28c14`  
Baseline: `58aec9f1439b9440d89fc442f8fc49cf5d7b9464`

## Contract

`src/wrench_harness/outcome_receipt.py` provides
`build_outcome_receipt(payload)` and `validate_outcome_receipt(receipt)`. The
public receipt is a frozen value containing canonical JSON and its SHA-256.
Build/validate results use `VALID`, `INCOMPLETE`, or `INVALID` plus bounded
structured error codes. Invalid input returns no receipt.

The v1 payload binds task/run IDs, optional snapshot and context receipt
SHA-256s, selected/omitted evidence IDs, retrieval miss statuses, actual route,
bounded model attempts, bounded verifier/tool work calls, verifier identity and
result/evidence, outcome status and provenance, correction references, and
accounting. Source/prompt text and hidden reasoning are not accepted fields.
Unknown usage/costs use null values and incomplete receipts list the missing
dimensions. Not-applicable and explicitly measured zero remain separate.

Attempt records reconcile local/frontier calls, retries, and fallback counts.
Verifier/tool calls have bounded individual records, so their summary totals
are checked against those records. Work calls on model routes join local and
frontier token/cost totals; deterministic work records explicitly mark model
token use not-applicable. Per-route token identities are stored separately,
allowing local and frontier counters to differ while requiring each route's
summary to match its per-call records. A timeout with missing usage cannot be
represented as zero. A no-call model attempt cannot report positive
exact/estimated token or cost use; retry references must point to an earlier
actual call; fallback counts include actual calls only. Independently verified
outcomes follow passed -> completed, failed -> failed, and inconclusive -> partial.
Deterministic route-none work records must state zero cost or unknown cost;
nonzero known model cost cannot be excluded from reconciliation.
The receipt is reference-only and makes no claim that reported or independently
verified outcomes are objectively true.

Limits: 64 KiB canonical serialized payload; 64 model attempt rows; 256 total
evidence/event/work references; 256-character IDs; bounded nesting and node
counts. Input containers require exact built-in types. Unknown schema fields,
raw-content keys, duplicate IDs, inconsistent totals, and malformed enum/hash
values fail closed.

Canonicalization deep-copies nested built-in dictionaries, lists, tuples, and
strings into a bounded owned tree, preflights that owned tree's exact encoded
size, then serializes the same tree. A deterministic test mutates caller-owned
nested data at the encoder seam and confirms the receipt retains the copied
value.

## Verification

Baseline commit verified before edits: `58aec9f1439b9440d89fc442f8fc49cf5d7b9464`.
Focused command used Python 3.11, bytecode and pytest plugin autoload disabled,
and temporary/cache output under
`C:\wrench-slm-data\tmp\W2-E0-OUTCOME-RECEIPT-20260924`:

```powershell
& 'C:\Users\stanc\AppData\Roaming\uv\python\cpython-3.11.16-windows-x86_64-none\python.exe' -B -m pytest -p no:cacheprovider tests/test_outcome_receipt.py
```

Result: `18 passed`. Only this focused test file was run. No model, provider,
network, install, inference, training, spend, credential, or external
communication was used. No commit was created.

Final storage status was `WITHIN_LIMIT`: 590,572,206 bytes actual plus the
20,000,000-byte active reservation, 610,572,206 bytes projected, with no
checker errors. C: had 186,288,582,656 bytes free.

## Caveats

The builder validates caller-provided structure and internal consistency. It
does not independently query snapshot/context ledgers, prove verifier identity,
confirm provider usage, recover missing measurements, or establish causal
attribution. Callers must supply those verified references before using a
receipt for later evaluation or learning.

## Reviewer repair

Job: `W2-E0-OUTCOME-RECEIPT-FIX-20260924`  
Nonce: `ORF-93d75a`  
Start commit: `58aec9f1439b9440d89fc442f8fc49cf5d7b9464`

Repairs add route-aware model-attempt usage checks, require retry targets to be
earlier actual calls, and reject fallback flags without a call. Fallback
totals count actual calls only. Independently verified outcomes must match the
verifier mapping passed/completed, failed/failed, or inconclusive/partial.
Accounting carries separate local and frontier token-counter identities and
reconciles each against per-call usage without collapsing mixed conventions.
Serialization now deep-copies supported nested built-ins into a bounded owned
tree, then preflights and encodes that exact tree. Concurrent dictionary
resizing during the copy fails as a typed invalid result. Deterministic
route-none work cannot report positive known model costs. Final focused run:
`28 passed`; scoped `git diff --check` passed. Storage at that run was
`WITHIN_LIMIT`: 590,585,211 actual, 20,000,000 reserved, 610,585,211 projected,
and C: free space 186,286,473,216 bytes. No commit was created.

## Independent acceptance

Review job `W2-E0-OUTCOME-RECEIPT-REVIEW3-20260924`, nonce `ORR3-ff315a`,
accepted the final version after verifying all reported repairs, including
typed rejection for concurrent dictionary resizing and rejection of known
positive model costs on deterministic non-model work. Final scoped hashes:

- `src/wrench_harness/outcome_receipt.py`: `8931C271895EFBD6F21B6BBF59CFF538E72D3D960B2FB76A48D5783DF48BD676`
- `tests/test_outcome_receipt.py`: `87345492BCD39BC4E990F94BAD824847D3BE59BC298854551997F1DF64BD3BFB`
- `docs/goal/wrench-e0-outcome-receipt/GOAL.md`: `8558236E612F6D4D376D15836EAF69A166F5EDED83FA4B12B3F92D29A6CC0994`
- `docs/reports/wrench-e0-outcome-receipt/receipt.md`: `5F6A25A127A0DD743222D5B3BDB782A4EB78004E8FB4668A4DE373F792B32946`

This is a reviewed metadata contract, not evidence that E0 is integrated or
that any caller-supplied outcome is true.
