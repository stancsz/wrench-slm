# Iteration 028: OpenCode 2.0.12 SubRoute HTTP hook observer

Date: 2026-09-27 (America/Edmonton)

Status: **SYNTHETIC HOOK UNIT CHECK PASSED; NO LIVE OPENCode REQUEST OR PROVIDER CALL**

## Scope and route

The owner reconfirmed the existing SubRoute at `http://127.0.0.1:4000`.
Read-only GETs in this task returned HTTP 200 from `/v1/models` and
`/api/active-model`; the model list contained 19 aliases and the active policy
reported `active_model=openrouter`, `mode=force`, `policy_version=4`. Those
fields do not provide generation usage, selected upstream provider, or billed
cost. The exact forced route remains a paid-capability path until proven
otherwise. No completion POST was made; no model or provider was invoked.

The installed OpenCode executable and package were previously verified as
`2.0.12`. The preceding capture accountant was incorrectly pinned to `2.0.15`;
its supported-version constant and fixture version are corrected to `2.0.12`.
The former iteration 027 receipt records the source identity at that time and
is left unchanged.

## Source-verified hook seam

OpenCode v2.0.12 prepares the protocol request, exposes `session.http.request`
as a Web `Request`, converts the hook-returned request body back to bytes, and
then calls the transport handler. This is the correct candidate seam for
observing the lowered HTTP body before transport. The public plugin API exposes
`ctx.session.hook("http.request", callback)` and returns a disposable
registration. Hooks run in registration order, so later request hooks could
still mutate the request. An eventual integration must use an isolated config
with the observer last and verify the actual loaded plugin order. These source
details are pinned to the [v2.0.12 request path](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/core/src/session/model-request.ts),
[plugin hook API](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/plugin/src/promise/session.ts),
and [hook registration behavior](https://github.com/anomalyco/opencode/blob/v2.0.12/packages/core/src/plugin/hooks.ts).
The [official plugin-build example](https://opencode.ai/v2/docs/build/plugins#overview)
uses a default export; the example module follows that loader contract.

## Prepared observer

`examples/opencode_v2_subroute_capture/` contains an opt-in example plugin and
a testable observer core. Its plugin module has a default export and registers
the public hook API. The example:

- is inert unless `WRENCH_SYNTHETIC_CAPTURE=1`;
- accepts only OpenCode `http.request` primary requests to the exact SubRoute
  URL and a fresh request containing one exact
  `WRENCH_SYNTHETIC_FIXTURE:<run_id>` user message;
- requires a pre-pinned digest of the entire normalized synthetic request JSON,
  covering system/developer instructions, tool schemas, and other request
  fields, and rejects duplicate JSON keys;
- rejects prior assistant/tool history and any mismatched route, request kind,
  marker, or oversized body;
- clones and reads the request without changing the original;
- writes only a content-free JSONL receipt under
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\opencode-http-capture`,
  with a per-run 2 MiB receipt cap and 2,048-request cap; and
- leaves tokens, provider identity, and cost null.

The example is not placed in an auto-loaded plugin directory or enabled in
either OpenCode config. This iteration did not exercise the plugin in OpenCode
and did not prove hook ordering, transport retries, episode closure, or complete
request capture. It is an integration component, not an effectiveness result.

## Verification

- `node --test --test-timeout=10000 examples/opencode_v2_subroute_capture/observer.test.mjs`: **7 passed**. It covers disabled-by-default behavior, content-free receipt creation, request-body preservation, wrong route/kind/marker/history rejection, duplicate-key rejection, full request-template pinning, bounded oversized-body rejection, and identity validation.
- `$env:PYTHONPATH='src'; python -B -m unittest discover -s tests -p test_opencode_request_capture.py`: **7 passed** after updating the OpenCode version pin.
- `node --check examples/opencode_v2_subroute_capture/plugin.mjs`: passed syntax validation. The `@opencode/plugin` runtime registration was not loaded.
- `git diff --check`: no whitespace errors; Git printed existing line-ending normalization notices for unrelated modified files.
- The first oversized-stream test exposed a pending clone-cancellation wait. The observer was changed to reject known oversized `Content-Length` before reading and not await clone cancellation on the streaming overflow path. The bounded negative test then passed. The only process stopped was the exact child process for this test.

## Evidence and limits

These checks establish synthetic hook-helper behavior only. They do not show
that a real OpenCode session used this plugin, that every retry or auxiliary
call was captured, that the provider received the same bytes after all hooks,
or that tokenization, task success, frontier usage, or billing was reduced.
The full-template allowlist digest and SHA-256 values in receipts remain
stable and linkable; receipts are content-free but not anonymous. The earlier
ratio-of-sums synthetic input result is not provider-token savings.

No model download, inference, training, benchmark, held-out access, private or
real-task capture, paid SubRoute request, adapter activation, or production
routing occurred. The latest host observation was 11.69% free RAM and 15,215
MiB free VRAM of 16,311 MiB. It clears the 10% operating floor but remains
below the active 25% LoRA-fit start gate. The LoRA and end-to-end 95/5, 95%
token/cost savings, quality, and all-day engineering goals remain unproven.

## Next evidence step

Use an isolated OpenCode v2.0.12 test configuration with a local mock transport
to prove plugin loading/order, exception propagation before the handler,
request-body identity, closure, and retry visibility without reaching port
4000. A separate paid matched comparison through SubRoute still requires an
owner-approved numeric aggregate USD cap plus caller-enforced hard budget and
provider/usage/billing receipts. The local LoRA fit remains behind its 25%
free-RAM, storage, candidate, and run-specific admission gates.

## Post-review hardening update

The first independent review (assignment
`WRENCH-OPENCODE-HTTP-HOOK-REVIEW3-20260927-01`, nonce
`d104693d-9505-4c22-a775-9caf07d06608`) returned **FAIL**. It found that the
caller supplied the expected digest and IDs, the observer did not block the
provider call, per-run files were unbounded in aggregate, and session/hash
metadata was linkable. That review applies to the initial implementation above.

The current implementation supersedes those mechanics. It uses the
source-controlled `synthetic-fixtures.mjs` digest and fixed IDs, verifies that
manifest against the exact test payload, removes session/request hashes, and
permits one receipt per arm at one of two fixed output paths using create-new
semantics. Each line is capped at 4 KiB. The enabled HTTP hook writes the
metadata receipt and then throws `provider_transport_disabled`. Local tests
verify the behavior of the helper, not exception propagation inside OpenCode.
The same running process accepts only one matching request per arm.

After this hardening, the Node observer suite passes **8/8**, the Python
accountant suite passes **7/7**, the plugin passes `node --check`, and
`git diff --check` reports no whitespace errors. Review 4 (assignment
`WRENCH-OPENCODE-HTTP-HOOK-REVIEW4-20260927-01`, nonce
`4b6425eb-c494-4661-a766-1fe8180db15f`) returned **CONDITIONAL** because the
path check was lexical and did not detect a Windows junction. The current sink
adds per-component `lstat` and `realpath` checks before and after directory
creation. Review 5 (assignment
`WRENCH-OPENCODE-HTTP-HOOK-REVIEW5-20260927-01`, nonce
`621b3df9-cba8-42b9-aa7b-85345bb6b6cd`) confirmed the new source-level path
redirection checks, fixed fixture provenance, content-free receipts, and 8
KiB aggregate ceiling. It remains **CONDITIONAL** because runtime tests did not
prove OpenCode propagates the hook exception before invoking its HTTP handler;
the path checks also cannot eliminate a local directory-replacement race.
Review 3's initial **FAIL** remains recorded and applies to the superseded
implementation.

OpenCode runtime loading, the effect of a thrown hook on the transport handler,
plugin ordering, retries, and episode closure remain unverified. No generation
call was sent to SubRoute port 4000. The earlier wording in this report
describing a caller-supplied digest and per-run 2 MiB sink refers only to the
initial version and is superseded by this section. At the latest recheck RAM
was 11.78% free and VRAM was 15,217/16,311 MiB free. No model load, inference,
training, or paid request occurred.
