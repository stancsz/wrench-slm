# Synthetic M3 context-token reduction protocol 06

Status: **frozen for one offline run**. Supersedes protocol 05, whose receipt
recorded a FAIL because the section-ID parser omitted Wrench’s `source-` ID
prefix; raw positive token pairs remain excluded under that screen. Protocol 04
completed with all positive cases excluded by the same oracle defect. Earlier
protocols 02 and 03 stopped before producing receipts. Explicit-operation proxy
protocols remain superseded and are not execution authority.

Job ID: `W2-SYN-M3-CTX-REDUCTION-20260925-05`  
Nonce: `SYNCTX07-D8F4`  
Runner: `tools/measure_synthetic_context_token_reduction.py`  
Runner SHA-256: `84bc138a8948e7c69b03b3e999d1c9ce886116af321d22a4642da5ffc46a9d3d`
Frozen one-shot output: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\synthetic-context-m3-reduction-05.json`

## Question and claim boundary

For seven exposed, Wrench-authored synthetic read/search tasks, how many
complete rendered input tokens does the deterministic E0 route-to-context path
use compared with placing the full source snapshot in the same downstream
prompt? Also, does E0 include the exact source evidence needed by each host-side
answer oracle and abstain on the frozen missing, stale, ambiguous, and
insufficient-context-budget boundaries?

This measures **synthetic MiniMax M3 tokenizer input reduction and deterministic
evidence-selection mechanics only**. It does not run a model, measure task
answer generation, establish real-work utility, reflect provider billing, or
measure frontier-token savings. The receipt must keep
`frontier_token_savings_percent` null and must not enter the paired frontier
savings reporter.

## Frozen prompts, tasks, and arms

- Fixture: `tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json`, with
  canonical SHA-256
  `871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5` and its
  admitted review receipt. Validate the manifest sidecar, review identity, and
  fixture admission before counting.
- Positive task IDs and pair groups: `loc-a`, `loc-b`, `triage-a`, `triage-b`,
  `context-a`, `context-b`, and `evidence-specific`. Each manifest `prompt` is
  the frozen deterministic router query. The downstream user question is the
  corresponding `CHALLENGE_CASES` prompt from
  `tools/run_local_synthetic_challenge.py`; verify that every positive ID has
  exactly one challenge prompt. Use that challenge question in both baseline
  and Wrench arms, preserving exact non-context message parity.
- Use the unchanged challenge system prompt from
  `tools/run_local_synthetic_challenge.py::SYSTEM_PROMPT`, SHA-256
  `5078f6f4ebadb81375726eca9cf7d34559165283517a7f7f5233d62cd020b2fa`.
  Verify its source file SHA-256 is
  `85c7857252814fe89a9f1bc08ce4432f09499f126dddb4692deb1922f1aafb56` by
  parsing only the two literal constants; do not import or run the challenge
  model runner.
- Baseline arm: same system and user messages, plus every exact source file in
  the case snapshot, sorted by path and labeled with its path, in one untrusted
  context message inserted at index 1.
- Wrench arm: same system and user messages, with the actual context message
  returned by `route_and_prepare_e0_context` from the same filesystem-backed,
  hash-bound source snapshot, inserted at index 1. Never construct it from
  answer labels, expected paths, or the expected route observation.
- Keep all non-context messages structurally identical. Route using the
  manifest query, then require route status/action/reason and complete
  observation dictionaries to match values independently derived from exact
  fixture bytes. For reads, derive path, UTF-8 byte count, and text. For literal
  searches, derive every ordered path/line/text match, full scope, and
  non-truncation. Require exact ordered evidence path/hash/byte rows and matching
  read attempt/success/byte counters before calling a positive successful.
- Recompute each required evidence ID from the snapshot hash, exact source
  path, and source SHA-256. Decode only the actual compiler wrapper. Each
  required path must have exactly one matching `[context:<evidence-id>]` section
  containing the entire exact source bytes. Each required oracle line and quote
  must be inside that same path/hash-bound section. For exhaustive literal
  search questions, require the full bounded search scope, including files
  with no matches. Wrench sections are rendered as `[context:<evidence-id>]`, a
  newline, then raw source text; do not add a `Path:` line or
  retain any bytes outside the ordered section join. The host-side oracle is
  checked after context construction and is never passed to routing or
  preparation.
- A positive case enters the token-reduction mean only if its route and
  preparation are ready, source identities join exactly, every required path
  and quote is visible, both prompt arms render, and the prompt-gate token count
  equals the independently counted complete Wrench message list. Record every
  failed positive as an excluded pair and as a failed evidence-selection
  outcome; exclusions cannot turn a failed acceptance screen into a pass.

## Boundary outcomes

These are outcome checks only and never token-saving pairs:

- `evidence-missing`: exact `source_not_in_snapshot` abstention.
- `evidence-stale`: exact `snapshot_read_changed` abstention. Materialize the
  pinned source, create the snapshot, then apply only the fixture's declared
  post-snapshot mutation before routing.
- `evidence-ambiguous`: exact `ambiguous_or_unsupported_request` abstention.
- `evidence-specific-context-budget-1`: reuse the frozen `evidence-specific`
  source case with context token budget 1 and prompt budget 8192. Require the
  expected `config/app.toml` read route, preparation `prompt_rejected`, and
  prompt-gate `required_evidence_omitted`. The recomputed evidence ID for
  `config/app.toml` must be absent from selected IDs and appear in gate and
  preparation omissions with reason
  `preserved_unit_exceeds_active_budget`; the gate must report
  `required_evidence_not_selected`, hard prompt budget 8192, and no token count,
  prompt hash, serialized byte count, prompt, or context message.

Every boundary must match its frozen reason/status and return no context. Any
boundary mismatch fails the local evidence-selection acceptance screen.

## Tokenizer and runtime identity

- Use the official `MiniMaxAI/MiniMax-M3` tokenizer at immutable revision
  `f0e1c1e04d40177e4673a22097036854f536e9c0`.
- The only selected repository assets are the nine files in
  `tools/fetch_minimax_m3_tokenizer_metadata.py`, totaling 16,884,564 bytes.
  The frozen repository inventory contains 82 files and 59 weight shards
  totaling 854,200,504,173 bytes. The tokenizer files already exist under
  `C:\wrench-slm-data\artifacts\wrench-local-acceptability\minimax-m3-tokenizer-f0e1c1e`.
  Do not download or load model weights, fetch more files, or create a second
  tokenizer cache copy.
- Before loading the tokenizer, verify the saved fetch receipt has status
  `TOKENIZER_METADATA_READY`, the pinned repository/revision, 82 repository
  files, 59 weight shards, the frozen total sizes, nine selected files,
  16,884,564 selected bytes, `model_weights_downloaded=false`, and inventory
  SHA-256 `86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`.
  Verify the receipt SHA-256 is
  `2d3b572b3f9b1667eb2b6944f35d72043e4c13f0061ac62f5db84e7893435398` and
  every selected file's exact size and SHA-256.
- Use the approved CPython 3.13.15 environment with Transformers 5.17.0,
  Tokenizers 0.23.2, and huggingface-hub 1.33.0. Verify runtime lock
  `tools/wrench-local-runtime-windows-cp313.lock` SHA-256
  `0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420`.
  Set Hugging Face and Torch caches under `C:\wrench-slm-data` and force
  offline mode. Load from the existing local tokenizer snapshot with
  `local_files_only=true` and `trust_remote_code=false`.
- For each complete prompt arm, call the pinned tokenizer chat template with
  `tokenize=true` and `add_generation_prompt=true`. Count through the
  generation prefix; do not make a model call or count generated output. The
  loaded template SHA-256 must be
  `11421244f67553498e5c8112dae02802025bcc4305ec45ad380af95c96f9fe64`.

## Metrics and outcome reporting

For each eligible positive task `i`, report `B_i` baseline and `W_i` Wrench
input token IDs and `100 * (1 - W_i / B_i)`. Report each pair, the arithmetic
mean of eligible per-task percentages, ratio-of-sums, eligible count, and all
excluded cases with reasons. Also report positive evidence-selection passes
out of seven and exact boundary passes out of four. A complete measurement may
return acceptance **FAIL**; it must not hide failed contexts by reporting only
the mean.

Keep `frontier_token_savings_percent` null and frontier usage pairs/calls zero.
Real frontier savings require participant-approved, repository-authorized
matched work, an independent task outcome, an authorized route, full request
lifecycle accounting, and complete usage receipts for both arms.

The receipt may retain only task/pair IDs, token counts, reductions, status and
exclusion codes, hashes, pinned identities, and bounded resource metadata. Do
not persist prompts, source text, rendered messages, answer values, quotes,
token IDs, or model output.

## Admission, one-shot rule, and stop conditions

- The current contract permits bounded offline checks over admitted
  Wrench-authored synthetic fixtures and public hash-bound package/model
  metadata. It prohibits training, model inference, provider/client calls,
  real-task capture, spend, publication, or production activation here.
- Use the already held reservation `W2-SYN-M3-CTX-REDUCTION-20260925-05` for
  30,000,000 peak additional bytes. Immediately before the job, recheck
  `python tools/check_wrench_storage_budget.py status`; projected aggregate
  use including every active reservation must remain below 50,000,000,000
  bytes. Confirm C: free space and at least 10% RAM and VRAM free.
- Run exactly once from committed measurement sources. The runner requires
  itself and this protocol to be tracked, and all tracked sources clean.
  The two pre-existing untracked owner files are outside this study and must
  remain untouched. Scratch and the sole output receipt stay under the approved
  artifact root. Do not retry or reuse this job ID.
- Frozen command:

  ```powershell
  C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe tools\measure_synthetic_context_token_reduction.py --output C:\wrench-slm-data\artifacts\wrench-local-acceptability\synthetic-context-m3-reduction-05.json
  ```

- Stop on any source, fixture, route, runtime, tokenizer, tokenizer-template,
  inventory, prompt-parity, source-identity, storage, or resource identity
  failure. A positive case that lacks required evidence or a boundary that
  abstains incorrectly is recorded as a failed outcome, excluded from token
  savings, and makes acceptance fail. Do not train, tune, call a
  model/provider/client, or send any request to localhost:4000.
