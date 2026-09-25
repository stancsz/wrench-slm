# Local patch-operations screen 01

Status: preregistration; execute only from the committed revision. Date: 2026-09-25.

## Question and claim

Can the deterministic route produce exact, unapplied review drafts for
replacement, append, insert-after, and explicitly requested whole-line
removal on fresh synthetic files, while abstaining at the frozen boundaries?

This is exposed open-development mechanics evidence. It is not a holdout and
does not establish semantic fix correctness, completed coding work, local SLM
capability, real-task utility, production readiness, or frontier-token
savings. A pass can support only these four deterministic draft operations
under the exact tested byte and prompt conditions.

## Frozen matrix

The exact prompts, source bytes, target bytes, file paths, per-case unified
diffs, and case identities are frozen in
`tools/measure_local_patch_operations_screen_01.py`. The 12 positives provide
three new fixtures for each operation, varying line or anchor positions and
surrounding content:

| Operation | Positive cases | Format and target-ending contract |
| --- | --- | --- |
| Replace | `replace_unique_value`, `replace_first_setting`, `replace_middle_setting` | UTF-8; LF-only; every source and target ends in LF; change only the exact unique old text. |
| Append | `append_first_record`, `append_middle_record`, `append_after_multiple_records` | UTF-8; LF-only; each prompt requires a new final line with one LF; source and target end in LF. |
| Insert after | `insert_after_final_anchor`, `insert_after_first_anchor`, `insert_after_middle_anchor` | UTF-8; LF-only; unique single-line anchor; source and target end in LF. |
| Whole-line removal | `remove_middle_whole_line`, `remove_first_whole_line`, `remove_final_whole_line` | UTF-8; LF-only; request says “remove the entire line containing”; source and target end in LF. |

The exact positive file bytes are (the strings below use escaped `\n` bytes):

| Case | Path | Source bytes | Target bytes |
| --- | --- | --- | --- |
| `replace_unique_value` | `config/runtime.cfg` | `timeout=8\ncolor=indigo\n` | `timeout=8\ncolor=chartreuse\n` |
| `replace_first_setting` | `env/service.conf` | `service=alpha\ncache=enabled\nretry=1\n` | `service=omega\ncache=enabled\nretry=1\n` |
| `replace_middle_setting` | `limits/request.cfg` | `connect=direct\nquota=4\ntrace=basic\n` | `connect=direct\nquota=7\ntrace=basic\n` |
| `append_first_record` | `notes/session.log` | `session=start\n` | `session=start\nsession=end\n` |
| `append_middle_record` | `journal/worker.log` | `startup=ok\ncleanup=pending\n` | `startup=ok\ncleanup=pending\ncleanup=done\n` |
| `append_after_multiple_records` | `events/router.log` | `event=ready\nhost=local\nowner=worker\n` | `event=ready\nhost=local\nowner=worker\nresult=complete\n` |
| `insert_after_final_anchor` | `runtime/boot.ini` | `prepare=base\nlaunch=fast\n` | `prepare=base\nlaunch=fast\nmetrics=off\n` |
| `insert_after_first_anchor` | `setup/environment.ini` | `environment=local\nlaunch=fast\n` | `environment=local\naudit=off\nlaunch=fast\n` |
| `insert_after_middle_anchor` | `pipeline/steps.cfg` | `load=core\nmode=safe\nflush=on\n` | `load=core\nmode=safe\nretry=never\nflush=on\n` |
| `remove_middle_whole_line` | `routing/proxy.ini` | `route=beta\nlegacy.endpoint=/v1\ntrusted=true\n` | `route=beta\ntrusted=true\n` |
| `remove_first_whole_line` | `profile/theme.ini` | `deprecated=amber\ncolor=blue\n` | `color=blue\n` |
| `remove_final_whole_line` | `selectors/legacy.ini` | `mode=fast\nobsolete.selector=old\n` | `mode=fast\n` |

Each exact unified diff is also frozen as `frozen_diff` beside its case in the
runner. The independent parser applies that literal diff to the source and
checks the resulting bytes against the target table.

The nine boundaries are `duplicate_replacement_target`,
`duplicate_insert_anchor`, `duplicate_whole_line_target`,
`missing_replacement_target`, `unsupported_unterminated_source`,
`unsupported_crlf_source`, `missing_whole_line_target`, `outside_root_path`,
and `malformed_apply_intent`. Their expected deterministic reasons, prompt
text and source trees are frozen alongside the positives:

| Boundary cases | Expected route reason |
| --- | --- |
| `duplicate_replacement_target`, `missing_replacement_target`, `duplicate_whole_line_target`, `missing_whole_line_target` | `patch_target_not_unique` |
| `duplicate_insert_anchor` | `patch_anchor_not_unique` |
| `unsupported_unterminated_source`, `unsupported_crlf_source` | `patch_source_format_unsupported` |
| `outside_root_path` | `path_outside_allowed_root` |
| `malformed_apply_intent` | `patch_draft_requires_review_only` |

The matrix includes
duplicate and absent targets/anchors, unterminated and CRLF source formats, an
outside-root path, and an immediate-apply request without review-only intent.

## Acceptance rule

- All 12 positives return `accepted` / `patch_draft` with exactly one expected
  relative path, the byte-for-byte frozen unified diff, and a deep TTC pass.
  The proposal and observation have `review_only=true`; the observation has
  `applied=false`.
- The screen-local diff parser checks the exact file headers, hunk position,
  line counts, source segment, and independently applies each diff. Applied
  bytes must equal the frozen target bytes.
- All nine boundaries return their exact expected deterministic abstention
  and no action. The receipt records `proposal_absent=true` only when the
  raw output parses as a JSON object with `status="abstain"`, the exact
  expected `fallback_reason`, and none of the proposal fields `schema`,
  `action`, `files`, `diff`, or `review_only`. Missing output, malformed JSON,
  or non-object output fails closed. The receipt keeps separate booleans for
  parse validity, proposal absence and payload/reason match. A model-not-loaded
  or generic fallback result fails.
- Every fixture file and directory identity is unchanged after routing.
- Any failed positive, boundary, exact-diff/application check, verifier,
  mutation check, or runtime case error makes the full screen fail. Run once;
  do not retry or repair after observing results.
- The receipt records hashes, booleans, reasons and timing only; it contains no
  raw prompt, source text, or diff text.

## Measurement identity and scope

- Job ID: `W2-LOCAL-PATCH-OPERATIONS-20260925-01`
- Nonce: `LPO01-SUPV-86C1`
- Protocol ID: `wrench.local.patch-operations.route-verifier.synthetic.v1`
- Runner: `tools/measure_local_patch_operations_screen_01.py`
- Receipt pins protocol, runner, route, worker, core verifier, TTC verifier,
  toolbelt, repository revision, and Python runtime version.
- No model or tokenizer load, inference, training, client, provider, network,
  model weights, real task data, or external usage arms.
- `frontier_token_savings_percent` remains null.

## Storage and resource admission

The parent job reserved 15,000,000 peak additional bytes under this screen's
unique job ID. Before the run, recheck storage status and confirm the
reservation remains active and adequate, check C: free space, and confirm at
least 10% system RAM and VRAM free. The route is CPU-only; VRAM is a
point-in-time reserve check. Use a new, empty scratch directory and a
nonexisting receipt path under
`C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability`. Recheck storage
afterward; release the reservation only after the job stops and the receipt is
accounted for. The runner writes only one case fixture at a time, cleans each
temporary case directory, and caps its JSON receipt at 1,000,000 bytes.

```powershell
python tools/check_wrench_storage_budget.py status
python tools/measure_local_patch_operations_screen_01.py --output C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\patch-operations-screen-01.json --work-root C:\\wrench-slm-data\\artifacts\\wrench-local-acceptability\\tmp\\patch-operations-screen-01
```
