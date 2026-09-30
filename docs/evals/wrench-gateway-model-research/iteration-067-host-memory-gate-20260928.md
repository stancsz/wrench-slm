# Iteration 067: diagnose the host memory gate

Timestamp: 2026-09-28 03:58 UTC (2026-09-27 21:58 America/Edmonton)

Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Current resource admission

The host sample measured 1,861.6 / 32,701.8 MiB free RAM (5.69%),
15,244 / 16,311 MiB free VRAM on the RTX 5060 Ti, and 140,502,839,296 bytes
free on C:. No Wrench training, inference, test, or benchmark process was
found. Storage was `WITHIN_LIMIT` at 10,991,532,059 bytes actual plus
8,103,000 bytes in active reservations before this report's 100,000-byte
reservation, `WRENCH-HOST-MEMORY-GATE-ITER067-20260928`.

The current use leaves a 1,408.6 MiB gap to the 10% RAM floor needed for an
independent review, and a 6,313.9 MiB gap to fit 03's 25% RAM start gate.
The exact-hash review was not dispatched; no Wrench run, test, or delegation
started.

## Host-memory source

A read-only process sample showed `vmmemWSL` at 15,564.9 MiB working set and
16,445.8 MiB private memory. `wsl --list --running --verbose` showed
`docker-desktop` as the only running WSL distribution; the Ubuntu
distributions were stopped. This identifies a large RAM consumer but does
not establish which containers or services depend on it.

The repository's host rules prohibit terminating Docker or WSL services
without explicit user authorization. I asked whether I may stop the
`docker-desktop` WSL distribution to try to release memory; it remains
running while that decision is pending. No other process was stopped.

## Next action

Keep the ACTIVE hourly heartbeat. If the user authorizes stopping
`docker-desktop`, perform only that explicitly authorized action, then take a
fresh RAM/VRAM/process sample. If RAM clears 10% with reserve headroom, submit
the already prepared independent 12-file fit-package review once. Start fit 03
only after that review passes and a fresh sample reaches 25% free RAM, with a
new storage reservation and at least 5 GiB destination headroom beyond it.
Without authorization, leave Docker/WSL running and continue provider-free
source work and hourly resource checks. The current preflight-05 runner and
protocol hashes still match, so do not repeat that preflight while their
identities remain unchanged.

SubRoute `http://127.0.0.1:4000` was not called. Paid generation remains
closed pending the campaign cap and fail-closed caller ledger. The Wrench
LoRA's quality, 95/5 task routing, 95% frontier-token savings, 95% all-in cost
reduction, and sustained engineering remain unproven.
