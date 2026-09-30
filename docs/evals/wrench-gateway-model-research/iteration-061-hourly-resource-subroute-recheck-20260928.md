# Iteration 061: hourly resource and SubRoute recheck

Timestamp: 2026-09-28 03:04 UTC (2026-09-27 America/Edmonton)

## Current resource admission

The fresh host sample measured 2,515.7 / 32,701.8 MiB free RAM (7.69%),
15,245 / 16,311 MiB free VRAM on the RTX 5060 Ti, and 140.77 GB free on C:.
The process query found no Wrench training, inference, or benchmark process;
the only pattern match was the PowerShell process running the query itself.
RAM is below the required 10% operating floor and far below the 25% fit start
gate. No tests, model runtime, inference, training, benchmark, or delegation
was run.

Storage status was `WITHIN_LIMIT`: 10,991,205,108 bytes actual,
8,103,000 bytes in active reservations, and no checker errors. A 100,000-byte
reservation for this bounded documentation update is recorded as
`WRENCH-HOURLY-GATE-RECHECK-ITER061-20260927`. It must be released after final
accounting.

## Owner-directed SubRoute check

At the owner's direction, the local endpoint was checked with read-only
requests to `http://127.0.0.1:4000/health/liveliness` and `/models`. Both
returned HTTP 200, and `/models` listed 19 aliases. Its `openrouter` row
exposed the alias but null context-length and pricing metadata. The check
proves local endpoint liveness only. It does not prove which upstream provider
will serve a generation or what the bill will be. No completion POST was sent.
The separate aggregate USD cap is still absent, so paid provider traffic stays
closed.

## Static fit-runner review

The current trainer source (`62319402F24721532EEECE095A298FFBD47DA7852CDE2B397589FFB48B3C13CC`)
was read around its resource monitor, optimizer loop, and finalization. The
monitor samples RAM, VRAM, and scratch every second and interrupts the main
thread on a reserve, scratch, or log-cap breach. The training loop checks the
breach state between batches and optimizer steps. Finalization re-reads the
resource log, checks GPU identity and resource floors, and can change an
apparent completion to `FAILED_RESOURCE_FINALIZATION`. The adapter is staged,
inventoried, checked against its size limit, and moved to the final candidate
path without replacement.

These are static source observations, not runtime proof. They do not replace
the missing independent exact-hash fit-package review. The protocol hash at
this check was
`EDAA9A20E66E18F005420B3F797EED085B002BB9E9AD266A5E75EE12DACE33B5` and the
scorer hash was
`0DD8B8A5AF6E22B6C4828E0C2465AB94DF7DBC3640E7DBAA8D17445F72A0F6E5`.

## Next action

The preflight 05 receipt remains the latest completed compatibility check as
documented in Iterations 008 and 060; it was not repeated. Fit 03 output was
not found, and no current package-review artifact was found in the eval/report
directories. The existing hourly automation remains `ACTIVE` and hourly.
Continue source-only preparation while RAM is below 10%. Once RAM is at least
10%, obtain one bounded independent package review. Start fit 03 only after
that review passes and RAM is at least 25% at start, RAM/VRAM remain at least
10%, storage is freshly admitted, and C: retains the required headroom.

No tests, provider request, or training run occurred in this iteration. The
LoRA's task quality, coding ability, 95/5 completion split, 95% frontier-token
reduction, 95% all-in savings, and all-day engineering remain unproven.
