# Iteration 179: direct-CUDA 4B scorer placement and preflight attempt 05

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Change and independent review

The 4B dev scorer previously loaded the BF16 model onto CPU and then called
`.to("cuda:0")`. It now uses the same direct CUDA device-map pattern as the
already-completed 4B fit and fails if either the base or adapter has parameters
off CUDA. The change affects placement only; model revision, tokenizer,
adapter, prompts, prediction protocol, resource monitor, and evaluation order
remain pinned.

Independent static review `WRENCH-4B-DEV-SCORER-GPU-PLACEMENT-REVIEW-ITER179-20260929`
(nonce `25d9c4a2-7942-4c8f-a4aa-3bbf8b4e1bd3`) passed for this diff. It verified
that reverting the loader lines reproduces the Iteration 176 scorer hash and
confirmed consistency with the fit trainer. The review does not establish
runtime behavior, successful inference, VRAM peak, quality, or savings.

| File | SHA-256 |
|---|---|
| `tools/score_gateway_lora_screen_03_4b_dev.py` | `2C430A1A1C52D3FA0118ACC2421A5D68CE3C665BA6EE40CE71BF400FA3AF2EE8` |
| Fit trainer | `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5` |
| Evaluation protocol | `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6` |

## Preflight attempt 05

Job `WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-05` used a fresh 500,000,000-byte
reservation, a new scorer output path, and the reviewed scorer hash. Admission
was 30.21% free RAM and 15,219/16,311 MiB free VRAM on the pinned RTX 5060 Ti.
After the first visible model allocation, the resource log sampled 26.37% free
RAM and 8,244/16,311 MiB free VRAM. Thus direct device placement avoided the
RAM collapse observed in attempt 04 at those samples, while consuming about
6.9 GiB of VRAM. It is not yet a full model peak measurement.

About 70 seconds after launch, both detached supervisor and scorer PIDs were
absent. The last resource sample is `2026-09-29T09:11:35.9039939Z`. The status
file is stale at `RUNNING` from 09:11:30 UTC, and an unfinished
`status.json.tmp` remains. The scorer output directory has no files, stdout and
stderr are empty, and there is no terminal receipt or prediction file. The
resource log SHA-256 is
`ABE792D413D37AE1ABE6AD8C8E6805AB42931EF85D5A7E669B9B16143C6C7C10`; the
temporary status file SHA-256 is
`3B1F7EE50D35584FA1DA95FCC3A2E272A58E347A0E4B1DCF958144A9EDA58CDD`.

This is an **incomplete local run with unresolved process teardown**. The RAM
and VRAM samples remained above the required 10% floors; the termination is
not a model-quality result or a resource-floor failure. No completed preflight,
model score, or provider call was produced. The exact process teardown cause
is not proven. Because this supervisor was started detached and its own status
write was interrupted, the next attempt will run its supervisor in the same
persistent foreground execution session and poll that session handle. Attempt
05 is one-shot and must not be reused.

## Accounting and next step

- The 500,000,000-byte reservation was released after checking that both
  process handles were absent and accounting for the supervisor logs, orphaned
  temporary status file, and empty scorer directory.
- Final storage status was `WITHIN_LIMIT` at 29,290,719,978 actual bytes plus
  6,103,000 bytes of active reservations. C: remained above the 5 GiB operating
  reserve.
- Final hardware sample was 30.44% free system RAM and 15,215/16,311 MiB free
  VRAM. It is a snapshot, not authorization for a future run.
- The current next step remains one fresh one-sample base/LoRA preflight using
  the same reviewed scorer and prompt, with a persistent foreground supervisor,
  new job ID, new reservation, 10% resource floors, and a bounded hard timeout.
  A passing preflight admits only the 64-row synthetic dev evaluation; it does
  not prove product coding performance, 95/5 routing, task-success retention,
  Frontier-token savings, cost reduction, or all-day operation.

See [Iteration 158](iteration-158-common-battery-qwen2b-vs-4b-20260928.md),
[Iteration 166](iteration-166-qwen35-4b-fit-01-20260929.md),
[Iteration 177](iteration-177-qwen35-4b-dev-preflight-interrupted-during-torch-import-20260929.md),
and [Iteration 178](iteration-178-qwen35-4b-preflight-resource-floor-and-next-candidate-20260929.md).
