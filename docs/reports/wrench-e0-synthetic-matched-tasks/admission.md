# Open synthetic fixture admission validator

Job: `W2-NS-SYNTH-ADMISSION-20260924`

Nonce: `ADMIT-9042`

Baseline: `45162350068eaf6541e15b1eec5dca995b1c0559`

Pinned canonical manifest SHA-256:
`871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`.

## Decision and scope

The prior read-only provenance/rights audit did not leave enough fields in the
v1 fixture manifest to distinguish development data from sealed/final data or
to validate split, lineage, and review state. The manifest was extended to
`wrench.synthetic-matched-tasks.v2` with explicit admission metadata. The
validator in `src/wrench_harness/synthetic_fixture_admission.py` recognizes one
origin and one requested use: `wrench_authored_synthetic_only` for
`open_development_fixture_only`.

It fails closed for unknown origin/schema, undeclared or disallowed use,
utility claims, sealed/final flags, any split except `open_development`, any
lineage except root Wrench-authored inline synthetic data, and review state,
scope, path, or receipt hash mismatch. The caller supplies review receipt
bytes; the validator hashes those bytes against the manifest. Current receipt
is the previously reviewed fixture evaluation at
`docs/evals/wrench-e0-synthetic-matched-tasks/review.md`, SHA-256
`b5c32928841b66aa679eccdbd7d88a4bffad4075b07f794f2a42d380961c1b2f`.
The implementation also pins the canonical manifest digest in source and
requires both the caller-supplied sidecar digest and the recomputed canonical
manifest digest to match it. This binds the accepted cases and inline source
bytes to the fixture identity; changing any field or source byte makes
admission fail with `fixture_identity_mismatch`.

The metadata schema is deliberately explicit:

- `origin`: exact synthetic origin constant.
- `declared_usage`: non-empty list limited to the one open development use.
- `sealed` and `final`: both must be the JSON boolean `false`.
- `split`: exact `open_development` value.
- `lineage`: authored inline synthetic root, with null parent manifest hash.
- `review`: mechanics review state and fixed scopes, with a fixed receipt path
  and SHA-256 checked against caller-supplied bytes.

The validator classifies this one fixture for local development checks. It
does not authenticate the manifest author or reviewer, prove rights or consent,
grant data-processing authority, or admit real/customer/public benchmark data
to any corpus. Its result is not accepted by the Phase 447 training corpus
validator and cannot admit training or sealed/final data. The receipt's review
scopes cover fixture integrity, mechanics, and oracle consistency only.

## Verification

Focused command:

```powershell
& 'C:\wrench-slm-data\cache\w2-rootbind-uv\archive-v0\j_0R9gSEmCfY82Cp\Scripts\python.exe' -m pytest tests/test_e0_synthetic_matched_tasks.py -q -p no:cacheprovider --basetemp C:\wrench-slm-data\tmp\pytest-synthetic-admission-20260924
```

Result: **7 passed** on the cached Python 3.11.16 / pytest 8.3.5 runtime.
Coverage includes the existing ten-case synthetic route/oracle suite, a valid
open fixture admission, and fail-closed mutations for unknown origin, missing
and disallowed usage, requested-use mismatch, sealed/final state, invalid
split/lineage/review state, review scopes, and receipt hash. No real data,
provider, model, client, or network was used.

An independent review first identified that metadata checks did not bind
admission to fixture contents. The digest pin and a changed-content regression
case were added in response. The final focused suite ran from the already
cached Wrench Python 3.11 environment under the approved data root.
