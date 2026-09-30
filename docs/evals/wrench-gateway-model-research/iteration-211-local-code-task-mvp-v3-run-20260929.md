# Iteration 211: local code-task MVP v3 run

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER211-20260929-01`  
Nonce: `cf00ee78-d600-4411-8a6f-23b5c7c7f869`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Exact identities

- Protocol: `docs/evals/wrench-gateway-model-research/iteration-211-local-code-task-mvp-v3-protocol-20260929.md`, SHA-256 `A12CC1F1380AA5F3B41213E405322250834010C810F632E673D59203EE0D810D`.
- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter211.py`, SHA-256 `19FF90E2B27EC0C1005492B5496C913C6B0985CC45AF16FD694513A0AB6CBD98`.
- Resource tests: `tests/test_gateway_torch_resource_sampler_iter211.py`, SHA-256 `2DF1134364AF0650FC72F579251F140584C02D109116A52323626ED566934F44`.
- Verifier regression tests: `tests/test_gateway_code_task_verifier_iter210.py`, SHA-256 `70913467E5C28D4D4EE6DCA71F7EB7BC6C24012F00D1CCF33220ADE1F7462DC8`.
- Receipt: `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\code-task-iter211-qwen35-4b.json`, 13,739 bytes, SHA-256 `47E198C1EAE3A9318C131C3E9F63AAD2CE8DD3842F990F9361AA7597CB73121A`.
- Fixture SHA-256: `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Snapshot SHA-256: `9a3b4f4540852918b58a4ece01d90451491b85f110aaef5436116fcdd37f2ca5`.

## Result

This completed pair compares one full-context prompt with one deterministic Wrench-prepared context for the same synthetic Python retry-delay repair. Both local-model outputs passed the restrictive AST verifier and six deterministic behavior cases, so the single episode retained the baseline's verified success. There was one generation per arm and no retry or recovery fetch.

| Arm | Input tokens | Output tokens | Total local tokens | Generation seconds | Verified |
| --- | ---: | ---: | ---: | ---: | --- |
| Full context | 8,805 | 85 | 8,890 | 36.3858 | Yes |
| Wrench context | 596 | 80 | 676 | 33.5782 | Yes |

For this one episode, input reduction was 93.2311%; input-plus-output local-token reduction was 92.3960%. The context builder's internal target counts were 8,803 and 594, respectively, two tokens below each rendered prompt count recorded by the model call. The savings above use the actual model-call counts, and the two-token discrepancy is retained for investigation rather than hidden.

Model-call success retention is `1/1` on this pair, not an estimated success rate. No frontier request was made. Frontier-token savings and all-in-cost savings are null, not zero or inferred from local tokenizer counts. The receipt records local compute energy and total cost as unmeasured. This does not establish any 95% product threshold.

## Runtime and safeguards

- Model: `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base, 14 pinned files, total inventory 9,342,907,469 bytes. The Wrench LoRA is not loaded; adapter remains inactive. This is an experimental local code-worker test, not the provisional bounded 2B controller or an all-day coding claim.
- Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2, NVIDIA RTX 5060 Ti, UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.
- Model load: 28.7257 seconds. Full run: 99.5445 seconds. Peak CUDA allocated/reserved: 11,592,906,240 / 12,127,830,016 bytes.
- Across 177 in-process samples, minimum free RAM was 19.4426% and minimum free VRAM was 21.3725%. No floor breach or sampler error was reported. Independent `nvidia-smi` pre/post VRAM readings differed from Torch by 1.3836 and 1.2991 percentage points, within the declared 10-point tolerance.
- The run forced the model offline, blocked Python socket connects (not OS-level network isolation), did not access held-out data, and did not modify the real repository. Frontier calls: zero.
- Storage status after the run was `WITHIN_LIMIT`: 32,709,079,602 actual bytes plus 186,103,000 bytes in active reservations, including this job's 150,000,000-byte reservation. C: had 124,805,447,680 bytes free. The receipt and this report are now counted; release this job reservation only after confirming the process is stopped and the final file sizes are counted.

## Checks and interpretation

The Iteration 211 resource-sampler tests, Iteration 210 verifier regression tests, and `git diff --check` were run before inference as recorded in the protocol. This report step did not rerun inference or tests. The v2 verifier accepts a single optional Python fence and safe docstring/annotation/local-assignment syntax, then checks behavior; its pass applies only to this fixture and those six cases.

This is a successful integration demonstration after two useful failed attempts: Iteration 209 exposed an overly strict verifier and both outputs failed; Iteration 210 aborted before a paired result when subprocess VRAM telemetry timed out. Iteration 211 fixes the monitor path and obtains a valid one-task pair. It does not prove representativeness, LoRA utility, sustained engineering, Frontier-token reduction, dollar savings, or a model-size winner. The 0.5B-12B comparison and full paired 95/5/95 acceptance study remain open. The provider route at SubRoute `:4000` is not used because its active route is forced to OpenRouter and the campaign spend cap remains absent.

The report binds the goal file actually present on disk. The heartbeat's separately stated goal hash `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` still differs; resolve that before any goal-bound package review or Fit-03 run.
