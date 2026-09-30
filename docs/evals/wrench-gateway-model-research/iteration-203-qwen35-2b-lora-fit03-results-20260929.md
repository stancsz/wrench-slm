# Iteration 203: Qwen3.5-2B LoRA fit 03 results

Date: 2026-09-29  
Disposition: **PASS for the bounded 96-step synthetic fit only**  
Adapter activation: **no**; held-out data opened: **no**; Frontier calls: **0**

## Result

The exact reviewed fit package completed three epochs and all 96 planned
optimizer steps on the RTX 5060 Ti. It trained a rank-8 LoRA on the Q/K/V/O
projections of the six full-attention layers, with 737,280 trainable parameters
out of 2,213,978,944 base parameters. It used 256 synthetic train examples
and 64 synthetic dev examples; the held-out split remained unopened.

| Epoch | Optimizer step | Train loss mean | Dev loss | Last gradient norm |
|---:|---:|---:|---:|---:|
| 1 | 32 | 0.533597 | 0.096066 | 1.655651 |
| 2 | 64 | 0.010022 | 0.038159 | 0.102281 |
| 3 | 96 | 0.000659 | 0.042163 | 0.011677 |

The training loss fell near zero and dev loss rose from epoch 2 to 3. This is
only a synthetic fitting diagnostic and may indicate overfitting; the dev
values were not used to choose a checkpoint, and they do not establish that the
adapter makes better gateway decisions. The adapter remains an inactive
candidate.

## Exact identity

- Job ID: `WRENCH-GATEWAY-LORA-SCREEN-04-QWEN35-2B-FIT-20260929-03`.
- Base: `Qwen/Qwen3.5-2B`, revision
  `15852e8c16360a2fea060d615a32b45270f8a8fc`.
- Model inventory SHA-256:
  `23E0D5F79E57D41AB9F007B697D8F75F56F5F528519BFDF15F406E1F28DF3DD5`.
- Candidate manifest SHA-256:
  `D4917EF337978B93D2220A9888CB4F640EDB63E54C8E49F70F0696B175DD2956`.
- Trainer SHA-256:
  `46E4F8ADED97EE0A4A524600CABFA089194767645169061D1500E9281662B3E5`.
- Protocol SHA-256:
  `6F06CF46EFE6862F8290D046E7327E79A085D3E9E05417871BBBAF00419A4B5F`.
- Dataset manifest SHA-256:
  `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED`.
- Train split SHA-256:
  `22F45C8B51EF680F9D05E8C42243EBB34E9F596B22D76577C64E371D272A39D2`.
- Dev split SHA-256:
  `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7`.
- Preflight manifest SHA-256:
  `EC7EA892935F6435124B355236418AFF95BD790F42CEF99688730829F4308667`.
- Preflight resource-log SHA-256:
  `A1E2802DB7E7ECBF84F7FF7368E60CEC3CF41420BF6922D8BF1CC3F5C1F3D17A`.
- Runtime: Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0,
  PEFT 0.21.0, Accelerate 1.15.0.
- Device: NVIDIA RTX 5060 Ti, UUID
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.
- Fit start RAM free: 29.40%; required: at least 25%.
- Resource samples: 1,910; minimum free RAM: 20.63%; minimum free VRAM:
  7,270 / 16,311 MiB (44.57%); runtime scratch peak: 0 bytes.
- Run manifest: 7,881 bytes, SHA-256
  `B20B13A869789A302819D6F4E40CE891FD13AC0111C485363E437956CFF52B86`.
- Resource log: SHA-256
  `2E450766400068A23C777601B44701E87BEF1052DF0072FA10BBB3ACF55812FA`.
- Epoch metrics: SHA-256
  `A7F7315966ACC88BE6A0A9CEE11C16BA991554F9F660AB86553A2D40F6EBF958`.
- Adapter files total: 2,962,573 bytes; `adapter_model.safetensors` SHA-256
  `1B679FEE96C31B066C9AD5D8912FD4A2BC024FF8665BE20B957D878CED8EBD41`.
- Storage reservation: 2,000,000,000 bytes, released after process exit and
  output accounting. The final storage scan was within the 50 GB limit.

## Interpretation and next gate

This confirms that the pinned 2B foundation and this adapter layout can finish
the bounded synthetic fit on this host while maintaining the resource reserve.
It took about 37.5 minutes, largely because the installed runtime used slower
reference implementations for missing optional fused kernels. It does not
prove useful decisions, a coding worker, 95% local task completion, a 5%
frontier escalation rate, Frontier-token savings, lower all-in cost, or
all-day engineering reliability.

## Model-size decision update

No parameter size is proven best for the complete product yet. The evidence
supports different candidates for different roles:

- **2B remains the practical gateway-controller lead**, because it has the
  lowest demonstrated latency in the existing three-task comparison (67.40 s
  versus 101.23 s for 4B), the current host completed its exact BF16 LoRA fit,
  and the base-plus-LoRA 64-row quality comparison is now possible. That
  three-task latency sample is small and its 2B arm did not use the new LoRA.
- **4B is the strongest near-term challenger for a local coding worker.** The
  official model card reports 55.8 on LiveCodeBench v6 and 50.3 on BFCL-V4,
  and Wrench's 64-row synthetic LoRA evaluation improved exact bounded
  decisions by 12.5 percentage points, mostly on compaction. It also regressed
  schema validity and route-field accuracy. See the [Qwen3.5-4B model card](https://huggingface.co/Qwen/Qwen3.5-4B)
  and [Iteration 197](iteration-197-qwen35-4b-dev-score-results-20260929.md).
- **9B is a capability reference, not a viable current installation.** The
  official model card reports 65.6 on LiveCodeBench v6 and 66.1 on BFCL-V4;
  its listed snapshot is about 19.3 GB. Current Wrench actual storage is about
  29.51 GB, leaving too little room below the strict 50 GB cap for the snapshot
  plus safe download/cache duplication and outputs. Do not download it under
  the present storage state. See the [Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B).

Therefore the practical next comparison remains 2B versus 4B on the same
frozen dev rows, with 4B as the stronger coding-capability challenger and 2B
as the smaller, lower-latency controller. Neither currently proves an all-day
coding worker or the 95/5 product target.

The next fair model-size comparison is to score the frozen 2B base and this
inactive adapter on the same 64-row prompt-only synthetic dev projection used
for Iteration 197, with the identical evaluator and accounting. Compare against
the reviewed 4B result: its exact-decision rate improved from 28.1% to 40.6%,
but schema validity fell 64/64 to 59/64 and route-field accuracy fell 55/64 to
48/64. Its gain was limited to compaction, so neither candidate can yet be
selected for the full gateway. Preserve the held-out data, keep both adapters
inactive, and separately evaluate mechanical context savings against actual
downstream usage receipts. Local tokenizer counts are not Frontier usage.
