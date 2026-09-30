# Gateway experiment iteration 002: LoRA preflight and training start

Date: 2026-09-27 (America/Edmonton)
Status: preflight passed; full local training is running
Goal: [gateway LoRA and token-reduction experiment](../../goal/wrench-gateway-model-research/GOAL.md)
Protocol: [LoRA screen 01](lora-screen-01-protocol-20260927.md)
Prior iteration: [synthetic corpus preparation](iteration-001-dataset-prep-20260927.md)

## Preflight identity and result

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-01-PREFLIGHT-20260927-01`
- Storage admission: 2,000,000,000 bytes reserved; released after the process
  stopped and its 96,563-byte receipt files were accounted.
- Base: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`; inventory SHA-256
  `64c38776f5d208c666e7033a0e121a63a240538f1f55b8865b5d31fddc474519`.
- Dataset manifest SHA-256:
  `11683129106ff2448930818d6631b8e76201798893e7587ecb0872cbf6bcebed`.
- Frozen protocol SHA-256:
  `de58a86a90ec829bab91d7189c470e1bf6d1f3e72fcd6f9e4c383463dd6bbacc`.
- Runner source snapshot SHA-256:
  `12a81f6202aaa597ef6fe72c15601397e0617fbe6a428ecc528f985329a5e0fc`.
  The byte-identical source snapshot is retained at
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-01\train_gateway_lora_screen_01.fit-source.py`.
- Environment: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0,
  PEFT 0.21.0, Accelerate 1.15.0, psutil 7.2.2. These add-ons live in their
  own directory under `C:\wrench-slm-data`; the base inference environment
  was not modified.
- Status: `PREFLIGHT_COMPLETED`; one optimizer step over eight examples,
  trainable parameters 5,411,328 / 858,397,248 (0.6304%), mean preflight loss
  1.7103. The run did not open the held-out split.
- Model load matched 186 text projection modules and excluded vision-only
  modules. Train and development inputs had a maximum observed sequence length
  of 338 tokens.

The step ran on CPU in FP32 with four threads and took 407.5 seconds. During
the monitored preflight, free RAM never fell below 8,544,391,168 bytes (7.96
GiB) and free VRAM never fell below 4,926 MiB. Peak RAM use was 23.98 GiB of
31.94 GiB. The 10% RAM/VRAM floors held. Transformers warned that the optional
`causal_conv1d` and Flash Linear Attention kernels were absent and used its
reference PyTorch implementations. The result establishes that this exact
small LoRA path can load and update safely on the host; it also shows low CPU
throughput. Linear extrapolation gives about 10.9 hours for the frozen 96
optimizer steps before development passes and final save, with substantial
uncertainty. This is a diagnostic, not a training-quality or engineering
capability result.

Receipt paths under the approved storage root:

- `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-01-preflight\run-manifest.json`
- `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-01-preflight\resources.jsonl`
- Run-manifest SHA-256:
  `2b81110ad6a32e5bf19ce078bfa3ea06231dfbf3d1ae0cf688e54039ceb97e93`.
- Final resource-log SHA-256 after the monitor stopped:
  `d3751d7d87d84649ea93daaa697f8c610386851e21a7c1eb09c519fbb5273ab1`.

The runner initially hashed the resource log before its monitor thread was
stopped, so the hash embedded in that preflight manifest (`bd4a578de2a40f12116300f72472c837cc7e008fcba53f5ed9aeb0be033d73bb`) is an earlier
prefix, not the final log. The final hash is recorded above. A finalization
step was added to the repository runner after this preflight; the running job
below uses the already-frozen source snapshot and will be verified against
its final on-disk log after it stops.

## Full training admission

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-01-FIT-20260927-01`.
- Storage reservation: 2,000,000,000 bytes, active before process start.
- Start time: `2026-09-27T08:34:03.658652+00:00`.
- Outputs are restricted to the one adapter under
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-01\adapter`
  and logs under
  `C:\wrench-slm-data\logs\wrench-gateway-model-research\lora-screen-01`.
- CPU FP32, four threads; `HF_HOME`, `TORCH_HOME`, `TEMP`, and `TMP` point
  under the approved storage root. No provider calls or public benchmark data
  are used. Training reads only the frozen train and development files; the
  runner records but does not open held-out examples.
- Latest observed run-manifest state at report time: `RUNNING_TRAINING`.
  No held-out score, adapter, local-completion rate, frontier-token saving, or
  95/5/95 outcome is available yet.

## Continuation snapshot, 2026-09-27 08:48 UTC

- Worker PID 5360 remained active. It had accumulated 3,185 CPU seconds since
  `2026-09-27T08:34:03.658652Z`; no epoch had completed, and no adapter output
  existed yet.
- Latest resource sample: 8,264,380,416 bytes free RAM (24.1%) and 4,875 MiB
  free VRAM (29.9%). These remain above the 10% floors. The exact run is
  monitored by the hourly heartbeat; no duplicate is admitted.
- Storage status: `WITHIN_LIMIT`, 10,953,393,830 actual bytes and
  2,011,588,760 reserved bytes, with 37,035,017,409 bytes aggregate headroom.
- A fresh read-only snapshot of `http://127.0.0.1:4000/api/active-model`
  returned `openrouter`, `force`, policy version 4. The owner specified this
  subroute, but a maximum USD cap is still missing. No generation request or
  paid provider usage occurred.

The training reservation remains active. The hourly thread heartbeat checks
for this exact active job before doing anything and must not start a duplicate.

## Continuation snapshot, 2026-09-27 09:11 UTC

- PID 5360 remained active after 8,027 CPU seconds. The manifest still reports
  `RUNNING_TRAINING`; there is no adapter output or score.
- Latest resource sample: 5,780,811,776 bytes free RAM (16.9%) and 15,094 MiB
  free VRAM (92.5%), both above the 10% floors.
- Storage status: `WITHIN_LIMIT`, 10,953,825,003 actual bytes and
  2,016,588,760 reserved bytes, with 37,029,586,236 bytes aggregate headroom.
  C: has 166,125,576,192 bytes free.
- A stale undefined-variable line in the held-out scorer was removed before
  any access. Python AST parsing and `git diff --check` pass. No held-out data,
  inference, or provider generation was used. Independent source-only review
  is pending for the exact scorer and protocol hashes.
- The scorer reservation remains active while that review is in progress.
  Training reservation remains active until PID 5360 exits and the final
  manifest, adapter, and resource-log hash are accounted.

## Continuation snapshot, 2026-09-27 09:24 UTC

- Fit PID 5360 remained active after 10,841 CPU seconds. The manifest reports
  `RUNNING_TRAINING`; no optimizer-step completion count or adapter is present.
- Latest resource sample: 5,708,787,712 bytes free RAM (16.65%) and 15,084 MiB
  free VRAM (92.48%). Storage remains `WITHIN_LIMIT`: 10,953,997,655 actual
  bytes and 2,016,588,760 reserved, with 37,029,413,584 bytes aggregate
  headroom. C: has 166,116,487,168 bytes free.
- Evaluator updates now disable PEFT for the base arm, reject timed-out
  development preflights, preserve failure receipts and partial-output state,
  enumerate valid decision mismatches, and report context metrics including
  only hot-preserving output as credited reduction. Static AST parsing and
  `git diff --check` pass; no held-out data or inference has been used.
- Independent review is pending for the final exact source/protocol hashes.
  Source reservation remains active until that review is complete.

## Superseding full-fit outcome (2026-09-27)

The subsequent screen-01 96-step CPU/FP32 fit did not complete. Its final
resource sample showed free RAM at 9.72%, below the 10% floor; no optimizer-step
count or adapter was produced. The monitor then failed through Python 3.13's
missing `threading.interrupt_main` API and recorded
`RESOURCE_MONITOR_ERROR:AttributeError`, masking the reserve breach. The
terminal receipt and resource log are retained; after verifying there was no
adapter or active process, the fit reservation was released. Screen 01 is a
failed fit, not an evaluation result. Held-out scoring remains sealed.

The follow-on GPU/FP32 candidate is separately frozen in
[screen-02 protocol](lora-screen-02-gpu-protocol-20260927.md). It has not yet
run its one-step preflight and has no adapter. Do not reuse this screen-01
preflight receipt for screen 02.
