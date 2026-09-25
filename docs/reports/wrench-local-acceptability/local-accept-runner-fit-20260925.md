# Local SLM acceptability runner fit

Job ID: `W2-LOCAL-ACCEPT-RUNNER-FIT-20260925`

Nonce: `LARF-7A29`
Repository HEAD reviewed: `3c9cb277a311e705e225c9322fd3f0d6bdd3ff2f`

## Decision

No existing runner can measure a new local SLM task class as-is. The current
prompt-only runner accepts only its frozen 18 cases in three exposed classes
and sends no evidence tools (`tools/measure_local_prompt_only_work.py:19-46,
120-156`). The local model challenge is tool-backed, but hardcodes the old ten
case IDs and only `read_file` / `literal_search` flows
(`tools/run_local_synthetic_challenge.py:65-106,
tools/run_local_synthetic_challenge.py:1220-1227`). The corrected Qwen run 02
completed 10/10 while making zero evidence-tool calls and passing 0/10; the
fresh prompt-only screen accepted 0/12 answerable cases and passed only three
of 18 whole cases, all correct abstentions
([run 02](local-slm-run-02.md#result),
[prompt-only result](prompt-only-local-work-screen-01.md#results)). Do not
retune, repeat, or repurpose either exposed fixture.

The deterministic patch-operation runner is useful executor evidence but not
an SLM harness: it constructs `WrenchWorker(tokenizer=None, model=None)` and
its receipt explicitly records `model_loaded: false`
(`tools/measure_local_patch_operations_screen_01.py:256-265,
tools/measure_local_patch_operations_screen_01.py:411-440`). Its accepted
scope is four exact review-only draft mechanics on open-development cases,
not generated patch quality
([local acceptance envelope](local-acceptance-envelope-20260925.md#decision),
[patch-operation protocol](../../evals/wrench-local-acceptability/patch-operations-screen-01-protocol.md#question-and-claim)).

## Recommended next screen

Preregister a new synthetic, tool-backed class for **one-file, review-only
configuration correction drafts**. Each positive case should require the
model to read a specified file with `read_file`, ground its proposed change in
that returned content, and emit one bounded `patch_draft`. A host-side oracle
should compare the exact target path and diff, independently apply the diff to
the fixture bytes, and require the target bytes to match while the fixture
tree remains unchanged. Require the same evidence-tool call and exact
abstention for frozen missing, stale, duplicate/ambiguous, outside-root, and
apply-request boundaries. Use newly authored paths, contents, prompts, targets,
and hashes, not any prior screen's cases.

This is a useful next capability to probe because Wrench already has a bounded
review-only draft action and exact diff-verification mechanics. The existing
patch runner checks deep TTC acceptance, `review_only=true`, `applied=false`,
and independently applied target equality
(`tools/measure_local_patch_operations_screen_01.py:297-317`). The SLM part
does not exist: the new runner must add the pinned local model, require an
actual read-tool event before accepting the draft, and score the independent
outcome. The old `run_local_synthetic_challenge.py` cannot simply take a new
manifest because its case IDs, expected calls, and execution path are fixed.

## Prerequisites and gates

- Freeze a new Wrench-authored fixture and reviewable independent source/target
  oracle before inference. Use at least six distinct positive examples and
  explicit no-action boundaries; keep the cases outside all model tuning and
  training. The class gate remains all cases exact, with grounded positive
  evidence, correct abstentions, and zero prohibited actions
  ([goal acceptance criteria](../../goal/wrench-local-acceptability/GOAL.md#acceptance-criteria)).
- Carry forward the already pinned Qwen/Qwen3.5-0.8B snapshot, 35-package
  runtime, tokenizer and chat-template hashes, serializer, resource checks, and
  25-minute supervised deadline from the accepted local-run protocols. Record
  exact tool/result events and per-case local prompt/completion tokens. The
  prior receipt pins model revision
  `2fc06364715b967f1860aea9cf38778875588b17`, runtime lock
  `0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420`,
  tokenizer JSON SHA-256
  `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42`,
  and serializer `direct_transformers.apply_chat_template.v1`
  ([run 02 identity](local-slm-run-02.md#identity-and-receipt)).
- Write a new runner and protocol. Add supervised hard-deadline execution,
  storage-reservation checks, 10% RAM/VRAM fail-closed checks, per-case
  checkpoints, exact output identity, and no retries. Validate the safe draft
  through the existing isolated executor/TTC path; never apply it to repository
  files.
- Current `COLLABORATION_CONTRACT.json` prohibits model inference without
  separate explicit authority. This review and its recommendation do not
  authorize the screen. Before a run, obtain that authority, reserve peak
  storage under the job ID, verify storage and destination space, and keep
  training disabled.

## Limits

A pass would establish only that the pinned SLM completed this fresh synthetic
review-draft screen. It would not establish coding correctness, real-work
utility, generalization, production readiness, or frontier-token savings.
There are still no matched frontier usage pairs; report savings as unavailable.
Training stays stopped until a preregistered held-out SLM class meets the goal's
full acceptance rule.

This report is a static runner/protocol fit review only. No inference, tests,
benchmark, client or provider request, model download, or fixture creation was
performed.
