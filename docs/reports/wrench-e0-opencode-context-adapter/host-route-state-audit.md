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

This is not proof of the live process route. The container may override the
state-file path through `ACTIVE_MODEL_STATE_PATH`; that environment value was
not inspected. The router loads state into memory at startup and request-time
snapshots use that in-memory state. The current host file therefore does not
prove which state the already-running process has loaded. No generation call,
gateway status request, runtime log, or provider observation was made.

The aliases contain no immutable weight revision, tokenizer bytes, or final
template identity. Token use or savings cannot be calculated from this static
configuration. No OpenCode prompt or inference was sent, and no credentials or
secret values were read.

## Evidence inspected

- `C:\Users\stanc\github\subroute\config\active_model.json`
- `C:\Users\stanc\github\subroute\config\litellm.yaml`
- `C:\Users\stanc\github\subroute\src\unified_llm_gateway\plugins\dynamic_router.py`
- Docker container metadata for port mapping and host mounts; environment
  variable **names only**, not their values

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
