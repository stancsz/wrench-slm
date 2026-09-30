# Iteration 221: separate bounded E0 source ingestion from selected context

Date: 2026-09-30 (America/Edmonton)  
Job ID: `WRENCH-E0-INGEST-CAP-ITER221-20260930-01`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Heartbeat-declared gateway goal SHA-256: `b847d638b0ca4f9c24041dccec2fb440861f0b27be0441e37e288057f701b027`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59` (mismatch)

## Change

Iteration 220 showed that E0 tried to fit all ingested source text into the same 8,192-token ledger limit used for its selected context. This stopped larger source sets before retrieval and packing could reduce them.

`prepare_e0_context` now accepts `source_ingestion_token_limit`. Its default remains 8,192 for compatibility. A caller may raise it up to a hard maximum of 65,536 tokens, but it must be at least the selected `context_token_budget`. The selected-context limit remains at most 8,192; the prompt gate remains at most 8,192. Existing path-count, per-source byte, aggregate source-byte, and prompt serialization bounds are unchanged. The source-ingestion limit is included in the content aggregate used for the preparation identity.

This changes deterministic E0 source admission only. It does not change the frozen foundation, installed Wrench-Core, any learned candidate, routing authority, provider access or execution permissions.

## Verification

Added unit coverage in `tests/test_e0_context_pipeline.py`:

- With the historical default limit, a synthetic source set above 8,192 word-estimate tokens fails closed with `ContextAdmissionError`.
- With ingestion raised to 16,384 and selected context kept at 2,048, preparation returns `READY`, retains the exact requested source marker and omits the unrelated noise.
- An aggregate source set exceeding the 65,536 hard cap fails closed even though each of its two noise files stays at the 64 KiB per-source byte limit.
- Limits below the selected-context budget and above the hard maximum are rejected as invalid input.

Focused E0/context integration run: **94 passed, 1 deselected**. The deselected existing lifecycle fixture requests OpenCode hook version 2.0.12, while the repository's `HEAD` E0 implementation accepts only `generic` or `opencode-2.0.15`; the mismatch is present in the checked-in baseline. The first broad run also caught a stale E0 public-signature allowlist; that allowlist now explicitly includes the new bounded parameter and the already-present `toml_span_query` field.

`git diff --check` completed without errors; Git printed only its existing line-ending normalization warnings for dirty files.

The focused unit test uses the context ledger's word estimate for source admission and a character-count prompt counter. It proves bounded ingestion and selection behavior, not an exact Qwen-token reduction percentage. The Iteration 220 frozen tokenizer screen was not rerun because the active-goal hash mismatch remains; its 12/12 failure and zero-savings fallback result remains unchanged. No model weights were loaded, no inference or provider call occurred, and no sealed data was opened.

## Identities

- `src/wrench_harness/e0_context_pipeline.py`: SHA-256 `7dbf627cec54c1f3fc8812ac2fd9e0893aa0c39dcfdbe5d531011f3796e666a2`.
- `tests/test_e0_context_pipeline.py`: SHA-256 `d9c6bd85b25515c25dbfc190bee1667379f0fbf13ec0179a846b4e179302b846`.
- Iteration 220 manifest (unchanged): SHA-256 `f80b48ce3269154f45735323d2f97cc8d2110de5b20800f286980f310046d9f4`.
- Iteration 220 tokenizer receipt (unchanged): SHA-256 `4a564c969424802d9f459748799011e0e6336a967652224fdbf50b7743a7f67f`.

## Next gate

Expose the same optional bounded setting through the relevant host-owned context wrappers while keeping their defaults fixed at 8,192. Then, once the active-goal identity is reconciled, rerun the frozen Iteration 220 tokenizer-only screen with an explicit ingestion cap and record prompt tokens, failures, omissions, latency and resource use before any model inference.
