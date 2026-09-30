# Iteration 077: host RAM and Docker footprint

Date: 2026-09-28 (America/Edmonton)

## Resource sample

- Free system RAM: 2,385.8 / 32,701.8 MiB (7.30%).
- Free RTX 5060 Ti VRAM: 15,191 / 16,311 MiB.
- Free C: space: 144,936,685,568 bytes.
- Fit-03 start gate: at least 25% free RAM, or 8,175.5 MiB. The current gap is
  5,789.7 MiB.
- Runtime floor: 10% RAM and VRAM. The current RAM sample is below that floor.

No tests, inference, training, benchmark, packaging, or delegation were
started.

## Main observed memory consumer

The top Windows process was `vmmemWSL` at 14,440 MiB. A read-only Docker stats
sample listed 26 running containers. Their largest observed working sets were:

| Container | Memory |
|---|---:|
| `canada-local-platform-ollama-1` | 2.381 GiB |
| `unified-llm-gateway` | 728.2 MiB |
| `unified-llm-gateway-staging` | 551.5 MiB |
| `unified-llm-gateway-experts` | 473.6 MiB |

Stopping the WSL distribution would interrupt every running Docker service,
including the user-directed SubRoute on port 4000. No container or WSL
distribution was stopped. The user was asked for explicit authorization for a
temporary WSL shutdown; absent that authorization, services stay running.

Storage status including the SubRoute checkout was `WITHIN_LIMIT` at
10,994,255,550 actual bytes before an 18,000-byte report reservation.

## Result and next gate

The experiment remains closed because free RAM is below both the 10% runtime
floor and fit-03's 25% start gate. The hourly monitor remains active and will
recheck fresh hardware status. Resume fit admission only after safe memory
headroom returns or the user authorizes a specific resource change, then
recheck all pinned identities, storage, destination space, and the full
fit-03 protocol. No model-quality, 95/5 routing, token-savings, or cost-savings
claim follows from this resource diagnostic.
