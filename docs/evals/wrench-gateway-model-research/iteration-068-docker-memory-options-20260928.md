# Iteration 068: measure Docker memory options

Timestamp: 2026-09-28 04:03 UTC (2026-09-27 22:03 America/Edmonton)

Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Current admission

The latest host sample measured 2,031.7 / 32,701.8 MiB free RAM (6.21%),
15,250 / 16,311 MiB free VRAM, and 140,308,824,064 bytes free on C:. No Wrench
training, inference, test, benchmark, or fit-review process was found.
Storage was `WITHIN_LIMIT` at 10,991,585,758 bytes actual plus 8,103,000
bytes in active reservations before this report's 100,000-byte reservation,
`WRENCH-DOCKER-RAM-OPTIONS-ITER068-20260928`.

The 10% RAM floor is 3,270.2 MiB, 1,238.5 MiB above this sample. Fit 03's
25% start floor is 8,175.5 MiB, 6,143.8 MiB above this sample.

## Read-only Docker footprint

`wsl --list --running --verbose` showed `docker-desktop` as the only running
WSL distribution. `docker ps` showed 26 running, healthy containers,
including SubRoute, unified gateway and staging, its experts service,
Ollama, Supabase, portal, and neighbourhood-platform services. A fresh
`docker stats --no-stream` sample reported:

| Container | Memory |
|---|---:|
| `canada-local-platform-ollama-1` | 2.382 GiB |
| `unified-llm-gateway` | 653.7 MiB |
| `unified-llm-gateway-staging` | 541.7 MiB |
| `unified-llm-gateway-experts` | 469.5 MiB |
| `supabase-studio` | 224.0 MiB |

The Windows `vmmemWSL` process was at 14,986.7 MiB working set in the nearby
process sample. Container memory figures do not guarantee an equal immediate
return of host RAM when a container or WSL is stopped. Stopping only Ollama
could plausibly clear the 10% review floor, but fit 03 would still miss 25% by
about 3.76 GiB even if all of its measured container memory returned to the
host. Stopping `docker-desktop` would interrupt all 26 listed containers,
including the requested SubRoute path and local development services.

## Authority and next action

No container or WSL distribution was stopped. Repository instructions require
explicit user authorization before stopping Docker or WSL. The user has been
given three choices: leave services running, stop only the Ollama container,
or stop the entire Docker Desktop WSL distribution. Wait for that decision.
The prepared fit-review packet was refreshed to bind the current GOAL hash
`2FE4368C6039695F469CF9DCBC4FD98394D7F5525601D7A029896D70CB801DA9` in its
12-file identity table; the existing assignment ID and nonce remain unused.

If only Ollama is authorized and stopped, take a fresh RAM/VRAM/disk/process
sample. Dispatch the prepared 12-file exact-hash review only if free RAM is at
least 10% with headroom. Fit 03 still requires the review to pass and at least
25% free RAM at launch. If all services remain running, keep the ACTIVE hourly
heartbeat and repeat read-only resource checks. Do not terminate any other
container or service implicitly.

No tests, model jobs, delegation, or provider calls ran. SubRoute
`http://127.0.0.1:4000` remains unused for generation pending the campaign
cap and caller-side ledger. The 95/5 completion split, 95% token/cost savings,
and sustained engineering ability remain unproven.
