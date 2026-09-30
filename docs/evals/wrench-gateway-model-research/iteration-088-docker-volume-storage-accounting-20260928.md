# Iteration 088: Docker Ollama volume storage accounting

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-EVAL-ITER088-DOCKER-VOLUME-ACCOUNTING-20260928`

Status: **storage path reconciled; model execution remains no-go on current
RAM and SubRoute integration evidence**

Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`

Gateway goal SHA-256: `225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Finding

Iteration 081 had identified the two Ollama tags in Docker volume
`local-ai-models`, but the Windows storage checker was not given an accessible
path for the Linux volume. This iteration resolved the path through Docker
Desktop's WSL file share. The exact directory is:

```text
\\wsl.localhost\docker-desktop\mnt\docker-desktop-disk\data\docker\volumes\local-ai-models\_data
```

`Test-Path` confirmed the directory exists. The storage checker successfully
walked it as an `--include-root` and counted **4,426,054,848 bytes**, matching
Iteration 081's `du -sb` total. The directory contains the existing Qwen3.5-4B
Q4_K_M and Qwen3.5-0.8B Q8_0 Ollama artifacts; this check did not read or
rehash the model blobs.

## Storage admission snapshot

The checker was run with both the Docker volume and the active hourly
automation included:

| Measure | Value |
|---|---:|
| Aggregate inventoried bytes | 15,418,738,774 |
| Existing active reservations | 6,103,000 |
| Status | `WITHIN_LIMIT` |
| Aggregate limit | 50,000,000,000 bytes |
| Remaining headroom before this report reservation | 34,575,158,225 bytes |

This closes Iteration 081's checker-path gap. For future storage checks and
reservations involving these weights, pass the same `--include-root` path.
The report reservation is `75,000` bytes under the assignment ID above.

## Runtime and routing boundary

The latest host snapshot showed **11.64% free RAM** (3,806.7 / 32,701.8 MiB)
and **15,187 / 16,311 MiB free VRAM** on the RTX 5060 Ti. RAM remains below
Fit-03's 25% start gate and too close to the 10% floor for a delegated package
review. The Fit-03 artifact and log directories remain absent, and no trainer
process was found. No model was loaded, trained, inferred, or benchmarked.

Read-only SubRoute checks to `/health/liveliness`, `/models`, `/v1/models`, and
`/api/active-model` returned HTTP 200. The catalog listed 19 aliases; the
active route was `openrouter`, forced, policy version 4. Iteration 081's
finding remains: `desktop` targets `ollama/qwen2.5-coder`, which is not an
installed tag, while the Ollama endpoint is unreachable from the gateway
container. These GETs do not establish a usable local model route, an
upstream completion, a tool round trip, or billed cost. No provider request,
credential read, service change, or restart occurred.

## Disposition and next action

The 4.426 GB Ollama volume is now included in the aggregate storage ledger, so
its unaccounted-storage condition is resolved for read-only inventory and
future admission checks. The model has **not** been shown to run smoothly, to
work through SubRoute, or to complete engineering tasks. Before testing it,
recheck system resources and maintain at least 10% free RAM and VRAM. Any
training run needs its own exact base revision and complete inventory,
LoRA-compatible runtime preflight, unique storage reservation, bounded
synthetic data, and output identity. Any SubRoute configuration change still
requires separate service authority; do not alter or restart the running
port-4000 service under this iteration.
