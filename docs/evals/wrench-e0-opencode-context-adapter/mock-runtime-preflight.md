# OpenCode synthetic mock runtime preflight evaluation

Job: `W2-NS-OPENCODE-MOCK-PREFLIGHT-20260926`, nonce `OC-MOCK-SUP-991E`
Reviewed revision: `0c7a00ab8cc4970ae66133d51bada7617fb7db90`

## Review result

The reviewed report is now limited to a plan for one success-only OpenCode
`v2.0.15` transport characterization. It uses the installed configuration's
provider and model identity (`wrench-local/current`, generic OpenAI-compatible
Chat Completions) through an isolated per-run config aimed at
`http://127.0.0.1:43117/v1`. It does not claim to test the separate E0 OpenAI
Responses research pin (`gpt-4.1-2025-04-14`). Port `4000` is excluded from
future requests.

No Wrench hook or plugin is registered in the installed CLI. The run uses one
Wrench-authored synthetic user instruction and measures the client's
downstream request plus canned response handling. It does not test Wrench
context insertion, transition receipts, callback failure, or dispatch veto.
The seven-field context envelope and `void | Promise<void>` callback return
are background API facts only. Neither is represented as a successful live
hook check. The mock may accept bounded client-supplied tool schemas but must
return no tool call; no tool execution is in scope.

## Independent reviews

Read-only API review job `W2-NS-OPENCODE-MOCK-API-20260926`, nonce
`OCMAPI-6A23`, verified the v2.0.15 context fields, callback type, current
installed provider/model identity, and source-derived compatible-chat path.
Read-only containment review job
`W2-NS-OPENCODE-MOCK-CONTAINMENT-20260926`, nonce `OCMCON-91D2`, confirmed
the existing synthetic fixture is offline-only and that loopback task
execution still needs explicit owner authorization. Neither worker ran a
test, changed a file, contacted a server, or launched OpenCode.

The independent report QA initially returned `NEEDS_CHANGES` for a port/config
mismatch, unsupported live-hook acceptance criteria, and combining the success
request with multiple failure runs. The report was corrected to use a
per-run config on port 43117, limit the first run to transport, and defer each
failure injection for separate authorization. Read-only re-review QA2
confirmed these three report corrections and requested the evaluation match
the transport-only scope. Read-only final evaluation QA job
`W2-NS-OPENCODE-PREFLIGHT-EGRESS-QA-20260926`, nonce `OCPEGQ-0394`, returned
**PASS** after this update and the report's explicit process-level
egress-confinement launch gate. The report also received a schematic request
and canned SSE example; final QA confirmed the pair still aligns.

## Preconditions and owner authority

The report specifies an isolated per-run config, launcher, endpoint, model,
synthetic input, response, and evidence. It also requires that the OpenCode
process connect only to loopback port 43117. A concrete, validated OS-level
egress-confinement mechanism has not been selected or exercised. Therefore the
plan is **not ready to launch**. Before any client invocation, select and
validate a process-level confinement mechanism that allows the mock connection
and prevents all other outbound connections; if this cannot be demonstrated,
do not run OpenCode.

After that technical precondition is met, the owner must explicitly approve
one success run with CLI `v2.0.15`, provider `wrench-local`, model `current`,
synthetic user text `Reply exactly MOCK_OK.`, mock port `43117`, one accepted
request and response, no credentials or plugins, no tool execution, and
bounded/redacted evidence under `C:\wrench-slm-data`. Each failure-injection
or live-hook run needs separate approval. This report grants no execution
authority.

The install config and E0 Responses pin remain distinct. Even if a future
transport run succeeds, it will not establish Wrench hook behavior,
request/tokenizer parity for the Responses target, customer utility,
production dispatch enforcement, or E0/E4 acceptance.

## Admission evidence

The 3,000,000-byte preflight reservation was active before these documentation
artifacts were created. Storage status with npm-cache explicitly included was
`WITHIN_LIMIT`: actual 2,280,564,978 bytes, active reservations 15,103,000
bytes, projected 2,295,667,978 bytes, headroom 47,704,332,021 bytes. At that
check, RAM free was 13,307,031,552 of 34,290,302,976 bytes (38.8%); RTX 5060 Ti
VRAM free was 15,177 of 16,311 MiB; C: free space was 181,846,130,688 bytes.
These are point-in-time readings. Storage, volume free space, and 10% RAM/VRAM
reserves must be rechecked and a new per-run reservation admitted before any
future client/mock artifact-producing job. After all five assigned doc/goal
artifacts were present, a second status still returned `WITHIN_LIMIT`: actual
2,280,661,579 bytes; active reservations 8,103,000 bytes (including this
3,000,000-byte reservation); projected 2,288,764,579 bytes; headroom
47,711,235,420 bytes. RAM free was 13,765,918,720 bytes (40.1%) and VRAM free
was 15,214 MiB. The later reservation release and final storage status are
reported in the supervisor handoff.

No OpenCode prompt, task, chat, request, inference, gateway request after the
recorded `/v1/models` GET, external provider call, test, or model work occurred
in this preflight. See the [plan report](../../reports/wrench-e0-opencode-context-adapter/mock-runtime-preflight.md).
