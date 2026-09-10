# Usefulness pilot progress

Updated: 2026-09-09
State: Blocked pending the cloud routing condition. No usefulness verdict yet. The same blocker persisted across three consecutive turns; the latest read-only live configuration check still returned frontier_percent=10, and the comparison run remains terminal with status failed.

## Completed engineering work

- The Pro SFT path now uses batched tensors, padding attention masks, completion-only supervision, actual validation loss when a validation split is supplied, finite loss/gradient checks, and bounded step counts.
- Oversized examples raise a descriptive error rather than silently losing input context or target content. Dataset construction must choose supported lengths before training.
- Model/tokenizer/optimizer/RNG states and the training contract are saved for isolated candidates. Tests reproduce uninterrupted weights exactly after a save/reload/resume cycle using a tiny Qwen model.
- The pilot has strict full-argument comparison and boundary validation. Explicit abstention and invalid output converted to fallback are separate outcomes.
- The initial pilot inference path is unconstrained generation followed by strict validation. It makes no claim of grammar-constrained generation. Legacy native serving, legacy FSM behavior, and GRPO remain outside this repaired path.
- Focused lint passed for changed Python files. The complete suite passed: 68 tests (latest run: 7.73 seconds).

## Real model diagnostic

Receipt: artifacts/usefulness-pilot/machinery-20260909/run.json

- Cached base: Qwen/Qwen2.5-0.5B-Instruct, revision 7ae557604adf67be50417f59c2c2f167def9a775.
- BF16 base on the local RTX 5070 Ti; LoRA rank 16, alpha 32, dropout 0.05.
- Budget: 8 optimizer steps, batch 1, accumulation 2, maximum sequence length 512, zero cloud requests for training.
- Completed 16 example presentations on five authored diagnostic examples.
- Peak PyTorch allocated memory: 1,752,904,704 bytes. This excludes other processes and is not the model's deployment memory claim.
- Fresh-process adapter/tokenizer reload reproduced all five training targets, including ROUTER_FALLBACK. Receipt: artifacts/usefulness-pilot/machinery-20260909/reload_diagnostic.json.

These observations establish a working selected training path. They do not establish generalization, model quality on independent tasks, or useful latency. Diagnostic full-call timings were roughly 0.3-1.5 seconds under the current unoptimized, shared-machine setup; no millisecond deployment claim is supported.

The diagnostic checkpoint predates the added formatter hash in the resume contract. Keep its original receipt and code hashes; it is not an approved resume seed for the updated contract. Subsequent candidates must use the current contract. The unit-tested resume result applies to the current implementation.

## Data-source finding

Receipt: artifacts/usefulness-pilot/source-audit-20260909/event_fields.json

A read-only field inventory of 86,626 gateway event records found no complete prompt, messages, input, context, request_body, or response_body fields. Some events have previews, which are not complete prior context. Existing raw tool-call records construct their prompts from the completed calls.

Therefore these sources can describe tool frequency and observed calls, but must not be relabeled as genuine pre-call intent examples. The pilot uses explicitly authored realistic tasks with independently defined outcomes. These cannot prove production traffic coverage.

## Gateway preflight finding

Receipts:

- artifacts/usefulness-pilot/gateway-preflight-20260909/receipt.json
- artifacts/usefulness-pilot/native-tool-preflight-20260909/receipt.json
- artifacts/usefulness-pilot/source-audit-20260909/gateway_preflight_events.json

A text-only request to minimax/minimax-m3 triggered Cheap Plus Rocket: 11 outbound contexts, approximately 25.5 seconds, and no standard response usage totals. Its requested max_tokens=32 did not bound all internal work. The event total counted original prompt tokens rather than the full sum of expanded prompts, so it cannot substantiate total cloud-token savings.

A native tool request used the supported ordinary path without changing gateway settings. Request 9b4db8f7 returned a read_file call, 404 prompt tokens and 43 completion tokens from provider usage, approximately 2.47 seconds observed wall time, and one correlated outbound context. No generated tool was executed during either preflight.

Next protocol requirement: keep real native tool schemas on every cloud turn, including post-observation verification, across all three arms. Record actual routing and usage. If the route expands into multiple calls or usage becomes incomplete, stop and report the accounting limitation rather than silently treating that call as comparable. The pilot will characterize this native-tool workflow, not general text-only Cheap Plus traffic.

## Dataset, candidate, and workflow completed

- data/pilots/authored-developer-v1 contains 640 training, 80 development, 80 calibration, and 120 evaluation scenarios. Evaluation has 24 wording families, 80 English cases and 40 held-out Chinese transfer cases. It is not 120 independent wording families. Manifests, token lengths, and isolation audits are preserved there.
- docs/reference/USEFULNESS_PILOT_PROTOCOL_V1.md freezes budgets, comparisons, scoring, and uncertainty methods. The small number of independent families limits the strength of any quality conclusion.
- Real disposable file, Git, search, and loopback HTTP environments are implemented. Writes register drafts only. Outcome checks require actual supporting tool observations.
- artifacts/usefulness-pilot/pro-candidate-v1 records one completed 150-step LoRA training run on the pinned pretrained base. No candidate selection used evaluation outcomes.
- artifacts/usefulness-pilot/development-v1 records unchanged-base development exact predictions of 7/80, candidate development 74/80, and candidate calibration 80/80. Candidate development errors concentrate in line-range tasks (4/10 exact). Prediction agreement is not final task success.
- artifacts/usefulness-pilot/workflow-smoke-v1 records an unscored development scenario completed by all three arms through real tool interfaces and four total cloud requests.

## Interrupted scored comparison

artifacts/usefulness-pilot/comparison-v1 preserves six episodes across two scenarios and ten cloud attempts. It is incomplete and must not be analyzed as the planned 360-episode comparison.

Request e7bfbb8d requested minimax/minimax-m3 but returned gpt-5.6-terra. Gateway logs correlate the request with a global-slider promotion at 10 percent and one outbound Terra context. The response contained provider usage of 594 input and 83 output tokens. The runner rejected the model mismatch and stopped, as protocol V1 requires. This is an experimental-control failure, not a demonstrated Wrench prediction failure.

Read-only inspection of the current gateway confirms that model names are hints and that explicit_bypass is deliberately ignored by the global slider. The normal chat endpoint has no supported model-pinning exception in the inspected path. Native tool schemas avoid the compound Cheap Plus path but do not prevent slider promotion. No production settings were changed to work around this behavior.

The analysis was invoked against the actual interrupted run with `.venv/Scripts/python.exe scripts/pilot_analyze.py --run artifacts/usefulness-pilot/comparison-v1`. It exited with `ValueError: Incomplete experiment; cannot issue a final comparative verdict`. Directory inspection confirmed that no summary.json or REPORT.md was generated. This verifies the incomplete-run guard on the real artifacts; it does not substitute for the pending complete comparison.

## Outstanding work

1. Resolve the cloud comparison condition: use a fixed-model endpoint for V1, or explicitly revise the protocol to measure the dynamic gateway workflow. A revised experiment must disclose routing as part of the system being measured and preserve this aborted run. Do not silently relax V1's model check.
2. Execute the complete matched comparison, retaining failures and all resource costs. Do not retrain the candidate or tune prompts using the two exposed evaluation scenarios.
3. Correlate gateway receipts, run the frozen analysis, and publish the supported verdict and limitations. Training loss, development scores, the smoke test, and the interrupted comparison do not establish usefulness.

The serving model, service configuration, existing root datasets, and sibling repository sources were not modified.
