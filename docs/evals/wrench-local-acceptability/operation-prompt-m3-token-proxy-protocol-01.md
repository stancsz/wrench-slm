# Explicit-operation synthetic M3 input-token proxy 01

Status: preregistered offline prompt-size measurement; no inference or provider use.
Job id: `LOCAL-M3-OPS-PROXY-20260925-01`
Nonce: `M3OP01-91A7`

## Question and claim boundary

For identical explicit read/search operation prompts, how many input tokens
does the snapshot-bound E0 route-to-preparation context use compared with a
direct full-snapshot context, when both complete message lists are counted
with the pinned MiniMax M3 chat template?

This is a **synthetic M3-tokenizer input reduction** proxy on tiny
Wrench-authored open-development fixtures. It measures prompt input size only.
It does not measure successful task completion, local SLM ability, real-work
utility, OpenCode request construction, provider billing, frontier-token
savings, or paid-cost reduction. `frontier_token_savings_percent` stays null.

## Frozen inputs and arms

- Fixture: `tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json`,
  canonical SHA-256 `871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`,
  with its existing mechanics review receipt. Select only the seven completed
  explicit operation cases: `loc-a`, `loc-b`, `triage-a`, `triage-b`,
  `context-a`, `context-b`, and `evidence-specific`.
- For each case, use its literal manifest `prompt` as both the route prompt and
  the final user message. The system message is fixed in the runner. Baseline
  and Wrench arms share identical system/user messages. Insert one context
  message at index 1, with role `user`, between system and user in both arms.
- **Baseline:** include every exact UTF-8 source file in that case's frozen
  snapshot, path-sorted, in one context message. Give each full file a path
  label and preserve all bytes. Use the same untrusted-context wrapper helper
  as the Wrench prompt compiler. This models direct full-snapshot context.
- **Wrench:** call `route_and_prepare_e0_context` on the exact snapshot using
  the unchanged operation prompt and the same base messages. Use only the
  returned `preparation.context_message_json`; never assemble it from expected
  paths or answer-oracle values. Require route status `JOINED`, preparation
  status `READY`, exact source identities and a non-null context message.
- Use the same untrusted-context wrapper implementation in both arms. The
  baseline labels every full-snapshot file with its path; Wrench uses the
  compiler's native `[context:<evidence-id>]` section format, which may omit
  path labels. Such a task is eligible only if every exact
  path and source quote required by its operation oracle is visible across the
  unchanged user message and the actual Wrench context message. Incomplete
  evidence is an exclusion, not a saving.
- For the empty literal-search case, eligibility requires every exact source
  text in the bounded search scope to be present in Wrench context. For a
  positive search, every returned match's exact path and line text must be
  visible. Use expected observations only after route/preparation to determine
  eligibility; never use them to construct the prompt or route.
- Compare the baseline/Wrench messages after removing context. They must be
  structurally identical. Both context messages must have role `user` and be
  inserted at the same position.

## Tokenizer and exact count

Use the already downloaded official `MiniMaxAI/MiniMax-M3` tokenizer files at
immutable revision `f0e1c1e04d40177e4673a22097036854f536e9c0`. Verify all nine
files against `source_inventory.json` and the prior fetch receipt before
loading. Use the installed CPython 3.13.15 / Transformers 5.17.0 / Tokenizers
0.23.2 environment and load only from the local tokenizer directory with
`local_files_only=True` and `trust_remote_code=False`. Do not download model
weights or create a second Hugging Face cache copy.

For each complete message list, call
`tokenizer.apply_chat_template(messages, tokenize=True,
add_generation_prompt=True)` and count the returned `input_ids`. If the result
is a mapping or batch wrapper, read its `input_ids` field and unwrap exactly
one conversation. Never count `len(BatchEncoding)`. Count through the
generation prefix; make no model call and count no generated tokens. Verify
the context compiler's tokenizer callback count equals the independent full
message-list count for every READY Wrench arm. Record the actual chat-template
SHA-256 and runtime package versions.

## Eligibility, exclusions and metric

Count a task only when both complete inputs render, E0 preparation is joined
and ready, all route-selected source hashes match preparation identities, and
the operation's exact path/text oracle is present as specified above. Keep
every exclusion with a bounded reason. The original natural-language
challenge prompts remain a separate protocol population; do not substitute
operation prompts into that study.

For each eligible case `i`, report `B_i` baseline and `W_i` Wrench input IDs,
then `100 * (1 - W_i / B_i)`. Report the arithmetic mean of per-task
percentages, ratio-of-sums `100 * (1 - sum(W_i) / sum(B_i))`, eligible count,
all exclusions, per-case and pair summaries. Zero or missing counts are
unavailable. Keep this proxy out of the paired frontier-savings reporter.

Persist only per-case IDs, token counts, reductions, eligibility/exclusion,
content-free hashes and identities. Do not store prompts, source text, rendered
messages or token-ID sequences in the receipt. No tuning or training on this
exposed fixture.

## Resource and stop conditions

All tokenizer assets and receipts remain under `C:\\wrench-slm-data`.
Immediately before the tokenizer-count job, check storage status and reserve
8,000,000 peak additional bytes with this unique job ID. Confirm at least 10%
free RAM and VRAM and sufficient C: free space. Check storage after the run;
release the reservation only after output accounting. Stop on any fixture,
review, source, tokenizer, template or runtime identity mismatch; route or
preparation error; prompt parity failure; tokenizer-count discrepancy; or
storage/resource reserve breach. Do not retry this job.

## Frozen command

```powershell
C:\\wrench-slm-data\\envs\\wrench-local-synthetic-cp313\\Scripts\\python.exe tools\\measure_operation_prompt_m3_proxy.py --output C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\operation-prompt-m3-proxy-20260925-01.json
```
