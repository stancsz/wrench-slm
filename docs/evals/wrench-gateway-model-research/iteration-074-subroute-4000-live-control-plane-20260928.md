# Iteration 074: SubRoute port 4000 live control-plane check

Date: 2026-09-28 (America/Edmonton)

## Request and result

The owner directed use of the existing SubRoute setup at `127.0.0.1:4000`.
Read-only `GET /health/liveliness` and `GET /models` both returned HTTP 200.
The model list contained 19 aliases. The checked-in `openrouter` alias maps to
`openrouter/minimax/minimax-m3`.

No completion request, credential read, or upstream provider request was made.
The campaign-wide USD spend cap remains unspecified, so no frontier generation
or comparative measurement was run.

## Live process identity and limitation

Port 4000 is owned by container `unified-llm-gateway`, using image
`ghcr.io/berriai/litellm-database@sha256:bd07ceb1fc7c4505f116c4eb2767956a8accba3119548dd8ae55e5356a381d56`.
The container bind-mounts the SubRoute checkout's `config` and `src` into
`/app/config` and `/app/src`. Docker reports the container start time as
`2026-09-25T21:52:44.437922193Z`. The mounted config was last modified at
`2026-09-27T18:46:18.8682373Z`, and
`src/unified_llm_gateway/plugins/openrouter_request_controls.py` at
`2026-09-28T05:15:07.295498Z`.

The current container therefore predates the mounted config and callback
changes. The GETs prove that the service responds, but not that its in-memory
LiteLLM process loaded the current request-controls callback or root-level
wire-body fix. The service was not restarted. Activation remains unverified.

## Resource and storage snapshot

- Free RAM: 3,479.3 / 32,701.8 MiB (10.64%).
- Free VRAM: 15,195 / 16,311 MiB (93.16%) on the RTX 5060 Ti.
- Free space on C:: 144,947,118,080 bytes.
- Storage checker: `WITHIN_LIMIT`, 10,994,085,927 actual bytes before the
  30,000-byte report reservation, with the SubRoute checkout included.

RAM remains below fit 03's required 25% free-RAM start gate. Held-out quality,
95/5 routing, retained task success, 95% frontier-token and all-in cost
reduction, and all-day coding ability remain unmeasured.
