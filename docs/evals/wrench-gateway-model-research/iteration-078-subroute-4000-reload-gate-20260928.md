# Iteration 078: SubRoute port-4000 reachability and callback reload gate

Date: 2026-09-28 (America/Edmonton)

## Result

The requested SubRoute control plane at `http://127.0.0.1:4000` is reachable:

- `GET /health/liveliness`: HTTP 200.
- `GET /v1/models`: HTTP 200 with 19 aliases.
- Docker reported `subroute-antigravity-1` healthy at roughly two days of
  uptime and `unified-llm-gateway` running at roughly two days of uptime.

These are GET-only control-plane checks. They establish that the existing
service responds, not that the callback edits are loaded or that a generation
would reach the intended provider. No completion request or provider call was
sent.

## Callback reload evidence

The current process predates the callback edits. Official LiteLLM v1.103.0
source initializes configured callbacks inside `ProxyConfig.load_config`.
Its periodic reload code describes model-cost-map and Anthropic beta-header
refreshes. The reviewed `/config/update` path persists config sections and
adds deployments, but the examined code does not show callback initialization
or plugin re-import. The official routing docs list settings that support
runtime updates, but do not document callback reload.

This is evidence that callback hot reload is not established, not proof about
the exact running image. The reviewed source tag is v1.103.0. Earlier source
parity work examined LiteLLM v1.101.0 for the Wrench adapter transform and
serialization path, but neither review inspects the live process. References:

- [Startup config load, LiteLLM v1.103.0](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L1133-L1145)
- [Callback initialization, LiteLLM v1.103.0](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L5413-L5544)
- [Periodic reload, LiteLLM v1.103.0](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L9400-L9416)
- [`/config/update`, LiteLLM v1.103.0](https://github.com/BerriAI/litellm/blob/v1.103.0/litellm/proxy/proxy_server.py#L15847-L16033)
- [LiteLLM routing and runtime configuration](https://docs.litellm.ai/docs/routing)

## Resource and spend gates

The fresh Windows sample showed 3,408.8 / 32,701.8 MiB free RAM (10.42%),
139.0 MiB above the 10% operating floor and 4,766.7 MiB below fit-03's 25%
start gate. C: had 144,692,109,312 bytes free. No test, inference, training,
restart, or provider request was run.

The owner has not authorized stopping Docker or WSL, and restarting the
gateway could interrupt the requested SubRoute service. The process was left
running. Recheck the loaded callback identity after an approved safe
restart/redeploy window, before any bounded synthetic generation. The
campaign-wide numeric USD cap is still unspecified, so paid comparison calls
remain closed.

## Interpretation

This iteration verifies local SubRoute reachability only. It does not verify
the active callback, provider/model routing, successful task completion,
frontier share, token or cost savings, or sustained engineering ability. The
95/5 routing, 95% task-success retention, 95% token/cost reduction, and
all-day engineering claims remain unproven.
