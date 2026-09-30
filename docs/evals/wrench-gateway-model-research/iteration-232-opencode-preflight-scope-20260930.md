# Iteration 232: define what the OpenCode capture preflight can prove

Date: 2026-09-30 (America/Edmonton)  
Job ID: `WRENCH-ITER232-OPENCODE-PREFLIGHT-BOUNDARY-20260930-01`  
Scope: static review of the provider-blocked OpenCode synthetic capture example; no tests, network requests, provider calls, model inference, training, or held-out access.

## Finding

`examples/opencode_v2_subroute_capture` is a hook and receipt **plumbing preflight**, not a paired context-preparation or token-savings experiment.

The synthetic fixture pins one `normalized_request_sha256`. `parseSyntheticBody` rejects every final request whose normalized JSON differs from that exact digest. The request builder in `plugin_setup.test.mjs` uses the same system text, marker, tools, and model for both arms. The arm is added to the receipt only after request validation; it does not select a distinct baseline or Wrench-prepared context. This fixture therefore exercises the same request template for each arm and cannot establish that context preparation reduced anything.

The registered HTTP hook calls the observer and then throws `provider_transport_disabled`. The plugin test confirms that no downstream HTTP handler runs. The response observer is called separately with a synthetic `Response` manufactured in the test. Its `input_tokens` and `output_tokens` are explicitly response-reported mock values, with `provider: null`, `billed_cost: null`, and `billing_verified: false`. They are not usage from the request just captured and cannot be counted as a frontier call or cost.

Together with Iteration 231, this gives two separate boundaries: the Python paired usage aggregator has a manifest-hash guard that lacks an end-to-end producer, while this OpenCode example has a fixed request hash and no transport. Neither produces a paired Wrench-versus-baseline task result.

## Evidence and exact identities

- `examples/opencode_v2_subroute_capture/observer.mjs`: SHA-256 `8894C2CE4899A9B872360F905182B847D061DDF107B540A3BB533BABBE7EABDF`
- `examples/opencode_v2_subroute_capture/synthetic-fixtures.mjs`: SHA-256 `AEB6D31260D2F5445BB7D495EC5E4A66B1470BFE27EF93CC42F67A770A08F58F`
- `examples/opencode_v2_subroute_capture/plugin_setup.mjs`: SHA-256 `E0D0ED9C61D281CC1C184CFE589EA0A692AA520A2EC9A90252D77F5CBC55BB0E`
- The reviewed test source builds one exact request payload and independently supplies a mock response; the test itself was not run during this audit.

## Correct use and next step

Keep this example's claim limited to safe hook registration, strict synthetic-request parsing, bounded content-free receipts, and fail-closed transport blocking. Do not compute a `frontier_token_savings` metric from these receipts.

The next paired evidence must come from a task runner that freezes a common episode manifest containing the task, fixture/source hashes, oracle/checks, split and pair ID, then renders arm-specific requests from that same manifest. It must bind the manifest digest into both arms and every usage receipt, preserve the distinct request-body hashes, record deterministic task outcomes, and count all retries. Any mock response remains labeled `mock` and excluded from provider calls, usage, billing, and the 95% gate. Actual provider comparison remains gated by the existing caller, route, budget and receipt requirements.

## Gate status

- This preflight does **not** measure input/output savings, task completion, frontier-call rate, billed cost, or all-day engineering.
- The current request observer can prove only its bounded local callback behavior when properly run in its approved synthetic setup.
- No SubRoute request was made. The SubRoute is forced to OpenRouter, and the campaign-wide spend cap is absent.
- No model work was done. The on-disk active-goal hash still differs from the heartbeat-declared hash.
- The paired identity producer, 95/5/95 outcomes, 95% full-lifecycle frontier-token reduction, 95% all-in cost reduction, and sustained engineering remain unproven.

## Execution record

Fresh storage status was `WITHIN_LIMIT`: actual `32,711,147,150` bytes, active reservations `36,103,000` bytes, and projected `32,747,250,150` bytes. It included the Docker Ollama model volume and this hourly automation directory. C: had `136,216,891,392` bytes free. The resource sample showed 38.74% free system RAM and 15,243/16,311 MiB free VRAM. Process search matched only its own PowerShell shell; no Wrench inference or training process was identified. A 20,000-byte reservation was made for this report and released after output accounting.
