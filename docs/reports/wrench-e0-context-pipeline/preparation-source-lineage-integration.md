# E0 preparation selected-source lineage integration

## Job record

- Job: `W2-NS-W2-LINEAGE-INTEGRATION-20260924`
- Nonce: `W2JOIN-C62D`
- Baseline: `405f72e36fa53648e02ac5146dd952cb30eb0464`
- Data: authored synthetic source files in focused tests only
- Client, provider, model, network, and training: not used

## Result

`PreparationResult` now has an optional `selected_source_references` receipt
and immutable `selected_source_reference_unavailable_reasons`. The preparation
path constructs the receipt after prompt compilation has produced the selected
evidence IDs, while the already validated `SourceIdentity` and
`StructuralCandidate` records remain in scope. It calls the committed
`build_selected_segment_source_references` API and never reads private
`ContextLedger` state.

Only IDs selected by the prompt gate appear in the lineage receipt. Source
segments carry normalized path, snapshot/content hashes, and artifact handle
ID with `span_status: whole_file` and null line bounds. Symbol spans carry
inclusive parser-reported lines only when the selected ID matches a validated
candidate joined to a successful source identity. The receipt contains no
source text. It does not treat parser coordinates as ground truth.

The preparation aggregate hash includes the lineage receipt digest and its
unavailable reason rows. The outcome receipt therefore binds the selected
lineage digest through its existing context-receipt hash. Missing source or
candidate joins produce an explicit `source_or_symbol_lineage_unavailable`
reason. Summary lineage remains unavailable because preparation does not
expose the ledger's `summary_of` input as a public selected record; this is
reported as `summary_lineage_not_exposed_by_preparation`.

If receipt construction fails validation or exceeds helper limits, preparation
returns `receipt_failed`, no prompt, and a typed reason. The default artifact
request scope still closes on return, so a handle ID is identity lineage, not
proof of a live pin. This is a local preparation receipt only: it does not
prove downstream prompt bytes, OpenCode/provider parity, dispatch, task truth,
or full E0 lifecycle accounting.

## Verification

- `tests/test_e0_context_pipeline.py` and
  `tests/test_selected_segment_sources.py`: 25 passed on Windows Python
  3.11.16 with pytest 8.4.2.
- Coverage checks selected source and symbol joins, exact parser-reported span,
  whole-file spans, summary-lineage unavailability, exclusion of an unselected
  second source, deterministic reruns, and preparation digest binding.
- `git diff --check`: passed; existing line-ending warnings only.
- Storage job reservation and final actual/projected bytes are in the handoff.

## Independent review

Read-only review passed under job `W2-NS-LINEAGE-INTEGRATION-REVIEW-20260924`,
nonce `W2REV-21E9`. The reviewer confirmed selected-only output, validated
source/candidate joins, parser-reported span labeling, bounded immutable
receipts and reasons, preparation aggregate binding, fail-closed construction,
and report scope. The reviewer ran no tests or edits. The helper API is tracked
in commit `405f72e`.
