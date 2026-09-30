# Iteration 231: audit the paired OpenCode episode identity gap

Date: 2026-09-30 (America/Edmonton)  
Job ID: `WRENCH-ITER231-CAPTURE-MANIFEST-GAP-20260930-01`  
Scope: read-only source audit of paired request capture, token-usage receipts, and current teacher-call gate. No tests, provider calls, local inference, training, or held-out access.

## Finding

Iteration 230 added a useful guard to `frontier_usage.py`: each usage receipt and usage arm carries a SHA-256 episode-manifest identity, and aggregation rejects mismatched arms. The guard is not yet connected to the OpenCode paired request capture path.

The current `RequestArmEpisode` in `src/wrench_harness/opencode_request_capture.py` contains only `pair_id`, `arm`, request captures, and a completeness flag. `capture_opencode_request` receives `pair_id` and `arm`, but no frozen episode manifest identity. Its receipt integrity payload therefore binds request bytes and routing metadata, not the canonical task/fixture definition. `aggregate_paired_request_bytes` matches arms by `pair_id` and common OpenCode version, route, and model alias. A reused pair ID with unrelated task fixtures is not rejected at this boundary.

That byte aggregator also explicitly returns `input_token_reduction_fraction=None`, `task_success_rates=None`, and `all_in_cost_reduction_fraction=None`; its body-byte ratio is marked as not being token reduction. It cannot support a frontier-token savings claim. The separate `frontier_usage.py` aggregator can compare response-reported token usage, but its manifest digest is still a caller-provided string. No source path found here constructs a canonical frozen task/fixture manifest and passes its digest through both request capture and usage aggregation.

## Source identities reviewed

- `src/wrench_harness/opencode_request_capture.py`: SHA-256 `5ADD10269DE39CB615656093ED13CDF4B61098736F89E6E6D76D189B9629928F`
- `src/wrench_harness/frontier_usage.py`: SHA-256 `5C9C2C13F495A011610293213E21E5EB26474AFD07DB3F99BD448A0FDD708001`
- `src/wrench_harness/server.py`: SHA-256 `CF86ED50DCA499438E71D98D1AE989F6B992BB4457226BE674AD0039F98BE6F9`
- `tools/capture_subroute_teacher_traces.py`: SHA-256 `8852DED137D07A5CF7E47F93E38CA310272EF0CE0E0B0EEA131A347925DC9AE6`
- `tools/run_teacher_call.py` currently returns `live_teacher_calls_disabled_until_aggregate_budget_and_durable_usage_receipts_are_enforced` without sending a request.

The SubRoute teacher capture source has an approval and budget-ledger implementation, but that is not authority to call it. No live response receipts or task outcomes exist in this audit.

## Required next implementation seam

Before any paired capture can be treated as episode-bound, define an immutable, canonical manifest schema covering the common task, fixture/source identities, acceptance checks, split and pairing identity. Construct and hash it from the frozen evaluation manifest, not from a caller-selected digest string. Make that digest a required field in both `RequestArmEpisode` and `UsageArmEpisode`, include it in capture integrity hashes, and reject missing, changed, or mismatched identities. Keep arm-specific prompts and request hashes as separate fields, since the actual baseline and Wrench prompts are expected to differ.

Wire the same verified digest from the task runner into both arms and each response-usage receipt. Add a negative regression for pair-ID reuse across different manifests and a positive regression for an identical manifest with different arm request bodies. Then report request bytes, response-reported tokens, verified task outcome, cost completeness, and billing verification as distinct measures. Do not promote a successful hash comparison to proof that task outcomes or provider bills are correct.

## Gate status

- **Paired episode identity:** not wired end to end; the acceptance-relevant source gap remains open.
- **Actual frontier token savings:** not established. Current request-capture output is byte accounting only; no authorized provider experiment or matched usage data was used here.
- **Provider-call gate:** closed. The existing call path is hard-disabled, SubRoute is forced OpenRouter, and the campaign-wide numeric cap is absent. No route, credential, or service was read or modified in this audit.
- **Model work:** not performed. The declared active-goal hash still differs from the on-disk goal-file hash, so no package/training identity was refreshed.
- **Product acceptance:** 95% local completion, <=5% frontier routing, >=95% success retention, >=95% full-lifecycle frontier-token reduction, >=95% all-in cost reduction, and all-day engineering remain unproven.

## Execution record

Before writing this audit, storage status was `WITHIN_LIMIT`: actual `32,711,121,443` bytes, active reservations `36,103,000` bytes, projected total `32,747,224,443` bytes. The check included Docker's Ollama model volume and the hourly automation directory. The audit reserved 20,000 bytes under its unique job ID on C:, which had `128,604,016,640` bytes free. Resource sample: 25.81% system RAM free and 15,213/16,311 MiB VRAM free on RTX 5060 Ti. Process inspection matched only the inspection shell; no Wrench training or inference job was found. The reservation is released after file accounting.

