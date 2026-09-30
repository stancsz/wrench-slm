# Iteration 085: host admission and hourly continuation refresh

Date: 2026-09-28 (America/Edmonton)  
Job ID: `WRENCH-HOURLY-ADMISSION-ITER085-20260928`  
Status: read-only resource and continuation-gate review; no model execution  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway-goal SHA-256: `225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## Current admission snapshot

The Windows host reports 32,701.8 MiB visible RAM and 3,430.6 MiB free
(10.49%). This is only 160.4 MiB above the 10% runtime floor and 4,744.9 MiB
below Fit-03's 25% RAM start gate. `nvidia-smi` reports an RTX 5060 Ti with
16,311 MiB VRAM, 15,202 MiB free. The GPU reserve is ample in this snapshot;
system RAM is the binding gate. A single near-floor sample is insufficient
admission for a delegated review, model load, inference, benchmark, or training.

The process inventory contains five generic Python processes. Their command
lines were not inspected, so this review does not attribute them to Wrench or
another task and does not terminate them.

The budget checker returned `WITHIN_LIMIT` after explicitly including the
SubRoute repository and hourly automation directory: 10,994,704,353 actual
bytes, 6,103,000 bytes of existing reservations, and no scan errors. The
25,000-byte Iteration 085 reservation was then admitted with those roots.
C: had 144,653,139,968 bytes free.

## SubRoute and continuation state

GET-only requests to `http://127.0.0.1:4000/health/liveliness`, `/models`,
and `/v1/models` each returned HTTP 200. These control-plane responses do not
prove which upstream provider serves a completion. No completion, provider
call, credential read, route change, or service restart occurred.

The existing `Wrench hourly gateway experiment` heartbeat is ACTIVE, hourly,
and targets this thread. Its current prompt contained the correct active
gateway-goal hash, but still described Iteration 084 and an older 8.49% RAM
sample. The prompt is refreshed to this iteration while preserving its
schedule, full success criteria, no-spend gate, route boundary, and resource
rules. The user-directed route is port 4000; an aggregate USD cap is still not
specified, so generation remains closed.

## Disposition

No model below 10B has been shown by this snapshot to run smoothly, and no
LoRA or token-saving claim is advanced by hardware telemetry. Fit-03 remains
closed until a fresh, sustained admission reaches at least 25% free RAM, all
other identity/storage/destination gates pass, and the exact package receives
the required review. Do not stop the observed Python processes or services to
manufacture headroom. Keep the hourly job active and continue provider-free
preparation between admission windows.

No tests, model loading, inference, training, benchmark, held-out data access,
provider call, or source-code change was made.
