# Selected segment source references

## Job record

- Job: `W2-NS-W2-SOURCE-REFS-20260924`
- Nonce: `REFS-BA32`
- Baseline: `45162350068eaf6541e15b1eec5dca995b1c0559`
- Data: inline synthetic identities and structural candidates in the focused test only
- Runtime, provider, client, network, and model: not used

## Result

Added `build_selected_segment_source_references` in
`src/wrench_harness/selected_segment_sources.py`. It consumes public
`PreparationResult.selected_evidence_ids`-shaped IDs, `SourceIdentity` rows,
and optional public `StructuralCandidate` rows. It joins selected source IDs
to path, snapshot hash, content hash, and artifact handle ID. Such whole-file
references have `span_status: whole_file` and null line bounds. A symbol row
receives inclusive parser-reported start/end lines only when a supplied
candidate matches the selected ID and the candidate snapshot, path, and source
hash match a successful source identity. Unknown IDs and absent candidate
lineage remain explicitly unavailable. Summary lineage is always marked
unavailable because this input seam does not provide `summary_of` records.

The receipt includes references and a canonical SHA-256 over the receipt body.
It contains no source text. The handle ID is an identity reference; it does not
prove that an artifact pin remains live. Parser-reported line spans do not
establish byte offsets or parser confidence. The signature segment’s content
is not reproduced in this receipt.

This is an additive helper, not connected to `PreparationResult` construction.
The current preparation return value discards structural candidates, so a
caller that has only that value cannot obtain symbol line spans through this
helper; those rows remain unavailable unless the exact candidate records are
also supplied. It does not prove selected IDs came from a particular assembly,
full prompt contents, OpenCode request parity, runtime dispatch, task outcome,
or full E0 lifecycle evidence.

## Verification

- `tests/test_selected_segment_sources.py`: 9 passed on Windows Python 3.11.16
  and pytest 8.4.2 using the existing approved-root test dependency cache.
- `git diff --check`: passed; Git emitted only existing LF/CRLF conversion
  warnings for unrelated dirty files.
- Storage admission: 10,000,000 bytes reserved for this job after a
  `WITHIN_LIMIT` scan. The focused test ran with 44.1% system RAM and 93.3%
  VRAM free. Final accounting and reservation release are recorded in the
  handoff.

## Review follow-up

The first independent review requested preflight bounds for source paths and
candidate parser/language metadata. The helper now validates these fields
before hashing or receipt construction and streams canonical JSON into a
bounded digest. The focused suite was rerun with eight cases, including
oversized source path and wrong-type/oversized parser metadata. A follow-up
review found that mutable internal reference rows could make the digest stale;
the helper now stores immutable mapping proxies and a regression checks this.
The suite was rerun with nine cases. Final read-only review passed under job
`W2-NS-REFS-IMMUTABLE-REVIEW-20260924`, nonce `REFS-IMM-1E0A`. The reviewer
confirmed immutable rows, bounded digest encoding, validated joins, and
accurate scope statements; the reviewer ran no tests.
