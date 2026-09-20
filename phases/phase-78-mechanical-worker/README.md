# Phase 78: mechanical-worker teacher capture

Status: `CAPTURED_PROPOSAL_ONLY_TRACE_REVIEW_PENDING`

This phase captured the current MiniMax-compatible teacher against the existing
220-case fixture so the next mechanical-worker iteration has a fresh, hash-bound
input. It did not execute any teacher proposal and it is not a final parity or
production receipt.

## Receipt

`teacher-traces-220-max768-replay.json`

- requests: 220
- transport failures: 0
- normalized Wrench proposals: 189
- invalid or unparseable outputs: 31
- observed length-terminated outputs: 3
- endpoint model id: `minimax`
- owner-supplied label: `MiniMax M3`, not independently identity-verified
- input suite: `evals/wrench-expanded-v1/cases.jsonl`
- SHA-256: `63f071156267d59aad2bbf1c5c2cc929338dc2b821f30b02696a62aa9a72569c`

The fixture is historical regression input. It is not the approved matched
real-workflow trace set. Proposal capture alone does not establish final task
success, verifier success, latency parity, token savings, or safe execution.
The next required step is to review and normalize valid teacher traces into
matched workflow arms, while keeping the sealed final split out of training and
candidate selection.
