# Host route-state audit for the OpenCode local profile

- Date: 2026-09-24 (America/Edmonton)
- Job: `W2-NS-E0-LOCAL-ROUTE-STATE-20260924`
- Nonce: `ROUTE-STATE-9C21`
- Evidence class: read-only host configuration/source inspection

## Result

The OpenCode profile points `wrench-local/current` at `127.0.0.1:4000/v1`.
Host-side Docker inspection shows port 4000 mapped to the container named
`unified-llm-gateway`, using image ID `bd07ceb1fc7c`, with host mounts for
`C:\Users\stanc\github\subroute\config` and `src`.

The inspected `config/active_model.json` currently says `active_model:
openrouter`, `mode: force`, and policy version 4. The mounted
`config/litellm.yaml` maps `current` to the virtual `openai/current` alias and
maps the selectable `openrouter` alias to `openrouter/minimax/minimax-m3`.
The mounted router source rewrites requests to the active alias in force mode.
Therefore the **inspected files** point `current` through OpenRouter's
MiniMax M3 alias, rather than establishing a local SLM route.

This is not proof of the live process route. A follow-up inspection of the
single non-secret `ACTIVE_MODEL_STATE_PATH` value found
`/app/config/active_model.json`, the mounted file listed above. Docker reports
the container started at `2026-09-23T14:22:01Z`; the host file's
`LastWriteTimeUtc` is `2026-09-23T22:08:09Z`, after startup. The router loads
state into memory at startup and request-time snapshots use that in-memory
state. The current host file therefore does not prove which state the
already-running process has loaded. No generation call, gateway status
request, runtime log, or provider observation was made.

The aliases contain no immutable weight revision, tokenizer bytes, or final
template identity. Token use or savings cannot be calculated from this static
configuration. No OpenCode prompt or inference was sent, and no credentials or
secret values were read.

## Evidence inspected

- `C:\Users\stanc\github\subroute\config\active_model.json`
- `C:\Users\stanc\github\subroute\config\litellm.yaml`
- `C:\Users\stanc\github\subroute\src\unified_llm_gateway\plugins\dynamic_router.py`
- Docker container metadata for port mapping, host mounts, start time, and the
  non-secret `ACTIVE_MODEL_STATE_PATH` value; other environment values were
  not inspected

Relevant source locations: `dynamic_router.py:25,113-145,183-230,258-275`;
`litellm.yaml:4-9,37-49`.

## Practical token-saving status

Verified Wrench token savings remain **not established**. No matched real-task
generation was run, and the inspected route is configured through a provider
alias if the mounted state is active. A percentage cannot be inferred
from a model alias, source-level route, synthetic character counter, or a
model-list response. Measure savings only after a consented matched-task run
with observed final request identities, paired usage accounting, and a task
oracle.

## Follow-up: live route-state snapshot

- Date: 2026-09-24 (America/Edmonton)
- Job: `W2-NS-ROUTE-READONLY-AUDIT-20260924`
- Nonce: `RRAD-7F20`
- Wrench repository revision: `167eb4df85110747e7ebdade02fb958eceda9166`
- Gateway source revision: `51d262370b3de790ee97ec6b9d43c33e4b44a2ee`

The route endpoint source was reviewed before making one local read-only
`GET http://127.0.0.1:4000/api/active-model`. The live response was HTTP 200:
`active_model=openrouter`, `mode=force`, `policy_version=4`,
`advisor_model=codex-sol-advisor`, with both reasoning-effort fields null.
Source `dynamic_router.py` SHA-256 is
`D20D3DB4FD23E78A5F26991F487808441BD097841D689D5E53E93500DAF5C12E`.
The handler returns a locked in-memory state snapshot; GET is separate from
the POST update handler. Its source enforces loopback access and rejects a
mismatched Origin. A gateway-wide authentication layer was not established by
the handler audit.

Docker reports the running gateway image as
`ghcr.io/berriai/litellm-database@sha256:bd07ceb1fc7c4505f116c4eb2767956a8accba3119548dd8ae55e5356a381d56`,
started `2026-09-23T14:22:01Z`, with the host `subroute\config` and `src`
directories mounted into the container. The mounted `litellm.yaml` has
SHA-256 `0DDCC4F32F7D0159913C152756172F16B6E37BC9171E860DFA2EE0F76A640AF0`
and a write time before container start. It maps `openrouter` to
`openrouter/minimax/minimax-m3`; the active route snapshot is consistent with
that configured alias. The active-model state file was not treated as proof
of runtime state; the GET supplied that state directly.

This establishes the gateway's active alias and force mode at one observation
time. It does not prove the exact upstream revision or tokenizer, the final
OpenCode request body, a completed upstream dispatch, billed usage, or token
savings. No prompt or upstream inference request was made. The route is not shown
to be a local SLM. Verified Wrench token savings remain **not established**.
