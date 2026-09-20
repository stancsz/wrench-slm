# Phase 81: 4M monster-payload mechanical retrieval

Status: `PASS_MECHANICAL_RETRIEVAL_DIAGNOSTIC_LLM_QUALITY_OPEN`

This phase stress-tests the embedded prefill toolbelt with one cold reference
payload near four million estimated tokens followed by a current intent. It
does not call an LLM. The result measures whether deterministic lookup can
preserve the current intent, find the old reference, and bind the selected
reference to its source hash before a model call.

The prefill index now uses two stages:

1. Cold ingest computes the full source hash and cheap size metadata without
   materializing every identifier in the payload.
2. Once the current intent is known, bounded query-term lookup extracts only
   relevant anchors and renders a small working set.

The final 4M stress receipt, `retrieval-4m-final.json`, reports:

- 3,999,951 estimated raw tokens
- 92 estimated model-prefill tokens
- 1.0 target-reference recall
- 1.0 current-intent preservation
- 1.0 hash-bound reference rate
- 98.713 ms cold ingest
- 44.441 ms hot selection
- zero model calls

The 220-case deterministic retrieval receipt remains a separate regression
diagnostic with 1.0 recall, 1.0 intent preservation, and 1.0 hash binding.
The earlier unoptimized 4M run took 5,089.089 ms cold ingest, so the change is
measured rather than a metadata-only claim.

These results prove the mechanical reducer and receipt path only. They do not
prove that an unchanged small model performs full-global-attention retrieval
over 4M tokens, nor do they prove MiniMax parity, final workflow success, or
production readiness.
