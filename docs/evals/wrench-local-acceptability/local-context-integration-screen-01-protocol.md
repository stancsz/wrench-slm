# Local context integration screen 01 protocol

Status: `NO RUN` until the orchestrator records fresh admission. This protocol
freezes a synthetic mechanics screen for caller-scoped E0 context preparation.
It does not evaluate a model or downstream task.

## Frozen inputs

- Fixture: `tests/fixtures/local_context_integration_screen_01.json`.
- Expected parent HEAD: `5a0d67f5f5bc94d8e0c5886bf0ba41b1e87150a3`. The
  measurement bundle must be the immediate child commit of this base. Record
  that child HEAD in the result receipt.
- Fixture SHA-256: `8f47a7d58473cf9db9778df6a43f06c0e753e166981a7b5909457242e1ab4949`.
- Runner SHA-256: `0f0d9f3c00599d3dfeff9f844f92c980c97c4b7b072ef9f9cdabd99bfc360838`.
- Committed pipeline source SHA-256:
  `0646c7b2ab2a2575e75e9eb5a94dde1146498d1f6b0da911fd4783f7f7a5e549`.
  The runner checks the runner, fixture and pipeline hashes supplied by this
  protocol. The operator passes the protocol file's separately computed
  SHA-256 because a document cannot contain its own digest. Any dirty
  worktree, unexpected parent, hash mismatch, incomplete inventory, or missing
  reservation means no run.
- The fixture-only serializer is identified as `fixture-json-v1`; it applies
  `materialize_prompt_messages` then compact canonical JSON serialization with
  `ensure_ascii=false`, sorted keys, and separators `,` and `:`. The fixture
  counter is `fixture-character-count-v1`: Python `len` of a string, or byte
  length for bytes. Both are test proxies, not a client serializer or tokenizer.
- No model, tokenizer, client, provider, network, credential, real project,
  real user content, or downstream work call is permitted or needed.

## Admission before any runner invocation

1. Confirm the fixture remains fresh and unexposed: it has not previously been
   run, scored, used to tune implementation, or used to select thresholds. If
   exposure or prior execution is discovered, mark it exposed and stop; never
   rerun this fixture. A later attempt requires a newly authored fixture and
   new identities.
2. Confirm exact committed HEAD and clean tracked source identities. Record
   hashes for the runner, fixture, protocol, and pipeline source. Resolve every
   TODO and validate the complete source/artifact inventory.
3. From the repository root, run
   `python tools/check_wrench_storage_budget.py status`, then reserve the
   measured peak additional bytes with a unique job ID using
   `python tools/check_wrench_storage_budget.py reserve --job-id UNIQUE_JOB_ID --reserve-bytes PEAK_ADDITIONAL_BYTES`.
   Include every Wrench-owned path outside the repository and approved data
   root with `--include-root`. Account for the runner, per-case source roots,
   artifact-store objects, logs, scratch, caches, and retained output together
   under the 50,000,000,000-byte ceiling. Check actual destination-volume free
   space separately. Status alone is not a reservation.
4. Verify actual host resources and keep at least 10% system RAM and 10% VRAM
   free. This synthetic CPU-only screen has no need to allocate a GPU; do not
   start if the host reserve cannot be established.
5. Keep all generated roots, stores, logs, and outputs beneath the approved
   `C:\wrench-slm-data` tree, within the admitted reservation. The fixed output
   path is `artifacts\wrench-local-acceptability\local-context-integration-screen-01.json`;
   the scratch root is
   `artifacts\wrench-local-acceptability\tmp\local-context-integration-screen-01`.
   Do not overwrite or remove existing data to make room.
6. The orchestrator must record the admission decision and allow one
   invocation. The runner atomically creates the fixed exposure marker
   `C:\wrench-slm-data\artifacts\wrench-local-acceptability\local-context-integration-screen-01.used`
   before creating case roots. It refuses later invocations even with a
   different output path. Retain the marker with the result. If marker creation
   succeeds but the runner fails before scoring, the fixture remains exposed
   and must not be rerun. Without the external admission record, status remains
   `NO RUN` and no case may be invoked.

## Case construction and exact oracle

Read the fixture as immutable input. For each case, create a new isolated
synthetic source root, write only its declared `source_files`, and create a
snapshot over exactly `snapshot_paths`. Apply the declared
`post_snapshot_mutation` only after snapshot creation. Use a fresh artifact
store for each case. Invoke `prepare_e0_context` once with the case's listed
paths, query, budgets, required and preserved paths, and the common fixed
arguments. Use an empty namespace registry and no schema lookups. The runner
deletes each synthetic source root and artifact store after checking it,
retaining only content-free result fields and hashes. Do not retry or alter any
case following an unexpected result.

Compare every field declared under the case's `expected` object exactly:
result status, route, prompt presence, prompt-gate status, reason, retrieval
miss statuses, outcome-receipt presence/status, and the positive case's source
identity and selected-evidence inclusion. Preserve receipt order when checking
ordered lists. The exact positive source identity is:

1. `content_sha256 = SHA256(exact UTF-8 source bytes)`.
2. `snapshot_sha256` is the hash returned by `create_snapshot` for that case.
3. `evidence_id = "source-" + SHA256(UTF8(json.dumps([snapshot_sha256, normalized_path, content_sha256], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)))`.
4. The returned source row for `src/alpha.py` has that digest and evidence ID,
   status `ok`, and the evidence ID occurs in `selected_evidence_ids`; the
   prompt and prompt gate are present and ready.

The deleted file must be reported as `missing`, and the changed file as `stale`
with no prompt. The two aliases in the duplicate case must reject with
`invalid_input` and reason `duplicate_normalized_path`. The budget case must
fail closed with no prompt, prompt-gate status `required_evidence_omitted`,
and required-evidence reason `preserved_unit_exceeds_active_budget`. All
successful E0 preparation receipts remain `incomplete` because no later task
outcome is observed. Any mismatch is a screen failure; do not change the oracle
or rerun the fixture.

## Interpretation and retention

This screen can establish only bounded synthetic integration mechanics for
source identity, retrieval misses, path-ambiguity rejection, required evidence
selection, and overflow fail-closed behavior. It cannot establish client
serializer/tokenizer parity, SLM competence, successful task work, production
acceptability, or frontier-token savings. Do not report the proxy character
count as model tokens or the E0 preparation result as a task success.

Retain only the bounded score receipt and required hash/admission metadata under
the reservation. Do not retain rendered prompts, full source text, answers, or
unbounded logs. Check storage during any prolonged orchestration and before
each output checkpoint; after the single invocation stops, account final files
and release the reservation. Mark this fixture exposed after invocation,
including an invocation that errors or produces no scores. Never rerun it.
