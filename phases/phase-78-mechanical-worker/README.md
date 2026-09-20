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

## Historical 220 model replay

The BF16 safety-calibrated 8E checkpoint was served through the 4M-configured
FreeToken overlay and replayed against all 220 rows using their original full
system and user prompts. The mechanical fast path was enabled.

Receipt: `wrench-safety-bf16-220.json`

- 220/220 requests completed
- 159/220 expected outcome matches
- 80/120 eligible exact proposal accepts
- 5 prohibited accepts
- 137/220 requests completed by the mechanical fast path
- median latency: 44.254 ms
- p95 latency: 10,034.813 ms
- 21 transport or runtime abstentions

Family-level results are uneven. `git_read_status` produced 29/30 outcome
matches, while `health_read` produced 6/30 and `patch_draft` 12/30. The five
prohibited accepts are in `read_file`, `literal_search`, and
`git_read_status`. The final split remains diagnostic because this is the old
fixture, not the new reviewed MiniMax workflow trace set.

The public BF16 native package was also smoke-tested separately. It accepted
the 4M endpoint configuration, but with a weak abbreviated system prompt it
repeated prompt text until the response cap and failed strict JSON validation.
That package is therefore a capacity artifact, not yet the selected worker
checkpoint. Receipt: `wrench-portable-smoke.json`.

After adding five prompt-aware fail-closed semantic guards, the same model and
same 220 inputs were replayed from a clean endpoint:
`wrench-safety-bf16-220-guarded.json`.

- outcome matches: 162/220, up from 159/220
- eligible exact accepts: 80/120, unchanged
- prohibited accepts: 0, down from 5
- mechanical fast-path requests: 137/220, unchanged
- median latency: 44.708 ms
- p95 latency: 10,044.587 ms

The five changed prohibited cases now abstain with explicit boundary reasons.
The remaining quality gap is concentrated in `health_read` and `patch_draft`,
plus slow model fallback paths. This is still historical diagnostic evidence,
not the matched MiniMax worker acceptance result.
