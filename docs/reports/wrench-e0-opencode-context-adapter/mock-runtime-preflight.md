# OpenCode synthetic mock runtime preflight

Job: `W2-NS-OPENCODE-MOCK-PREFLIGHT-20260926`
Nonce: `OC-MOCK-SUP-991E`
Prepared: 2026-09-24 (America/Edmonton)
Repository revision reviewed: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`

## Purpose and boundary

This plan prepares one future, owner-authorized OpenCode `v2.0.15` request
using Wrench-authored synthetic input and a local mock. It is not an execution
receipt. No OpenCode prompt/task/chat/inference was run for this preflight.
The user authorized installation/configuration and only the recorded GET
`http://127.0.0.1:4000/v1/models`; do not send any further request to port
4000. No external provider request, credentials, spending, real repository
content, or participant data is in scope.

The isolated install configures provider `wrench-local`, package
`@opencode/ai/providers/openai-compatible`, base URL
`http://127.0.0.1:4000/v1`, and model `current`. Its pinned v2.0.15 route is
OpenAI-compatible Chat Completions at `/chat/completions`, streaming enabled.
The E0 research pin separately names OpenAI Responses and
`gpt-4.1-2025-04-14`. The proposed first run is a separate transport
characterization of the installed `wrench-local/current` Chat Completions
configuration. It does not validate the E0 Responses pin or query the gateway.

For that run, create a fresh, bounded profile under
`C:\wrench-slm-data\opencode\W2-NS-OPENCODE-MOCK-RUNTIME-20260926\` with
an isolated `workspace\opencode.json` containing the same provider/model
mapping but `settings.baseURL` set to
`http://127.0.0.1:43117/v1`. Launch the installed binary through a dedicated
job wrapper that redirects all user/XDG/OpenCode/cache/log/tmp paths into that
fresh profile and explicitly points `OPENCODE_CONFIG` to this file. Do not
use the install wrapper unchanged because it pins `OPENCODE_CONFIG` to its
port-4000 setup. Record config and launcher hashes before execution; do not
copy service state or credentials. The mock is exactly
`127.0.0.1:43117`, bound to loopback only, and must refuse to start if that
port is unavailable. Its candidate endpoint is
`POST http://127.0.0.1:43117/v1/chat/completions`. The exact config source and
endpoint must be confirmed from isolated `debug config` evidence before
starting the client.

## Synthetic fixture and mock contract

Use only a Wrench-authored fixture derived from
`tests/test_opencode_hook_projection.py::_hook_event`, reduced to:

- model reference `{providerID: "wrench-local", id: "current"}`;
- synthetic session ID `ses_projection123` (shape fixture only, not proof of
  full upstream session-ID grammar);
- a Wrench-authored system message instructing the agent to return the exact
  string `MOCK_OK` and not call tools;
- one user text message: `Reply exactly MOCK_OK.`;
- one simple named agent, an empty tool map in the offline projection fixture,
  and bounded options with temperature `0`.

For a future OpenCode invocation, the one synthetic user instruction is the
only authored task input. The installed agent may add its own system context
and tool schemas. Bind those as runtime-generated request fields; do not dump
them into the durable report. Tool definitions may be present in the request,
but the canned response must contain no tool call, and no tool may execute.

The runtime context event has seven semantic fields, in any object-key order:
`sessionID`, `system`, `messages`, `agent`, `model`, `tools`, and `options`.
The pinned Promise hook is an awaited callback returning `void | Promise<void>`
that may mutate the supplied context. It does not return a replacement event
or typed admission/veto result. No Wrench plugin or live context hook is
installed, so this first run measures only the OpenCode request path after a
synthetic user input. It does not inject prepared Wrench context or verify
Wrench's offline transition receipt. The actual request body can contain
client-generated defaults; capture and compare the request boundary without
claiming hook projection parity.

After owner authorization, bind OpenCode and the mock to loopback only on
port `43117`, provided a pre-run exclusive bind check succeeds. The mock
accepts one bounded request only: `POST /v1/chat/completions`, JSON, configured
model ID `current`, one synthetic user message, and `stream: true` as required by the
pinned compatible-chat route. Permit protocol-required fields only after the
tagged body schema has been checked. Allow a bounded tool-schema array if
supplied, but return no tool call and do not execute any tool. Reject an
unexpected host, route, method, model, extra request, body over 1 MiB, or any
auth header; capture method/path, status, request count, body size/hash, and a
redacted allowlisted field summary (including message-role counts and tool
count/schema digests, not full system/tool contents). Never log auth values.
The minimum request fields are shown schematically below; the actual runtime
may include client-generated system messages, tools and generation options:

```http
POST /v1/chat/completions
Content-Type: application/json

{"model":"current","messages":[{"role":"user","content":[{"type":"text","text":"Reply exactly MOCK_OK."}]}],"stream":true}
```

Return a canned SSE response with content `MOCK_OK`, finish reason `stop`, and
`[DONE]`, for example:

```text
data: {"choices":[{"delta":{"content":"MOCK_OK"},"finish_reason":null}]}

data: {"choices":[{"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

This response is authored fixture data, not model output. Keep request and response
logs under a reserved job directory below `C:\wrench-slm-data`.

The source references are the tagged
[compatible provider](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/ai/src/providers/openai-compatible.ts),
[compatible chat route](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/ai/src/protocols/openai-compatible-chat.ts),
[OpenAI chat body lowerer and stream schema](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.15/packages/ai/src/protocols/openai-chat.ts),
and [context hook type](https://github.com/anomalyco/opencode/blob/v2.0.15/packages/plugin/src/promise/session.ts#L20-L33).
These source references do not substitute for observing the installed runtime.

## Success and failure observations

On the separately authorized success case, require all of the following:

1. The saved config source evidence shows the exact isolated runtime config,
   `wrench-local/current`, and the fresh mock URL. The CLI version and config
   hashes match the pre-run manifest.
2. The local mock records exactly one accepted `POST` on the selected route,
   with no auth header, configured model ID, synthetic user message, and
   source-conformant streaming body. No connection reaches port 4000 or any
   non-loopback destination.
3. The canned SSE response is accepted and the local CLI reports the literal
   fixture response `MOCK_OK`; no tool execution occurs, regardless of whether
   the request included tool schemas.
4. The evidence contains exact CLI/package/config identity, mock address and
   source route pin, process outcome, request count/body hash, response status,
   bounded log paths and hashes, and storage/resource receipts.

Failure-injection cases are out of scope for the requested first success run.
Each later mock-rejection, malformed/error SSE, callback-failure, or context
mutation case that invokes OpenCode needs separate owner authorization and a
new one-request limit. In particular, preparation callback failure and
protected context mutation are not executable in this transport-only run,
because no Wrench plugin is installed. Do not infer a dispatch veto from an
internal Wrench `READY`/failure classifier, a source trace, or one observed
absence of POST. The context API has no typed Wrench admission result.

## Admission and exact owner authorization still needed

As of this preflight, no concrete process-level egress-confinement mechanism
has been selected or validated. This plan is **not ready to launch**. Before
any OpenCode invocation, select and validate a mechanism that permits the
mock connection to loopback port 43117 and prevents every other outbound
connection. If that cannot be demonstrated, do not launch OpenCode.

Immediately before any future artifact-producing execution, use a unique job
ID and fresh reservation, run storage `status` (including npm-cache), then
`reserve` for the peak of mock/client logs and temporary files, and check C:
physical free space. Preserve at least 10% free system RAM and VRAM during the
run. The preflight-time inventory was `WITHIN_LIMIT`: actual
2,280,564,978 bytes, existing reservations 15,103,000 bytes, projected
2,295,667,978 bytes, headroom 47,704,332,021 bytes. System RAM was 13,307,031,552
of 34,290,302,976 bytes free (38.8%); RTX 5060 Ti VRAM was 15,177 of 16,311
MiB free. C: had 181,846,130,688 bytes free. These are point-in-time readings
and must be refreshed at execution admission.

No run is authorized by this plan. Approval is needed for one success-only
OpenCode request using CLI `v2.0.15`, the isolated config hash pinned in the
future run manifest, provider `wrench-local`, model ID `current`, endpoint
`http://127.0.0.1:43117/v1/chat/completions`, and the single authored user
instruction `Reply exactly MOCK_OK.`. The temporary config and wrapper must
remain under the per-run job directory; the process may connect only to
loopback port 43117; set no credentials or plugins; execute no tools; permit
exactly one request and one canned response; and retain bounded, redacted logs
and identity/resource receipts under the approved root. Never contact
`127.0.0.1:4000` during this run. If process-level egress confinement or the
single-request bound cannot be guaranteed, do not launch the client. Failure
injection and Wrench hook/dispatch behavior require separate future approval.
A passing run would establish only the tested local client's observed
Chat-Completions request and canned-response handling. It would not establish
Wrench hook behavior, provider/tokenizer parity, customer utility, production
dispatch enforcement, the Responses research pin, or E0 acceptance.

Review and future authorization requirements are captured in the
[preflight evaluation](../../evals/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md).
