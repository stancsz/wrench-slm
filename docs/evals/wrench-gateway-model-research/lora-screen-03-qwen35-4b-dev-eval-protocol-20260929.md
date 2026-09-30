# Qwen3.5-4B screen-03 answer-blind dev evaluation

Status: **protocol and source package only**. This file does not authorize an
evaluation run. No dev inference, scoring, provider request, or held-out access
has been performed by this package authoring task. The fit candidate remains
inactive.

## Question and scope

Compare the frozen Qwen3.5-4B base with the exact inactive fit-01 LoRA on the
same synthetic development prompts. This is a narrow check of whether the
adapter learned the bounded decision schema and labels in its authored
synthetic domain. It cannot establish coding ability, useful context
compression, engineering reliability, paid-token savings, cost savings, or
product acceptance.

The runner implements two separate one-shot jobs:

1. `preflight`: use at most the first dev prompt, once with adapters disabled
   and once with the LoRA enabled. This checks local inference and artifact
   bindings only. It does not read references for scoring.
2. `score-dev`: after a successful matching preflight, run both arms on all 64
   dev prompts. Flush and hash both raw-prediction files before parsing the
   references. The model receives only each row's `system` and `user` messages.

The source runner is
[`score_gateway_lora_screen_03_4b_dev.py`](../../../tools/score_gateway_lora_screen_03_4b_dev.py).
Its exact hash is recorded in the source-repair report and at run time in each
receipt. `score-dev` requires that hash and the protocol hash to match its
preflight receipt.

## Frozen input identities

| Input | Pinned identity |
|---|---|
| Repository base | HEAD `af01304824f079a64b6c3902397a2034b843511a` |
| Base | `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` |
| Model inventory | SHA-256 `30B09CF32F06FAE5418A0B925820202BFDDF9E1C2A1F009D12E6396D10AED15A`; 14 files, 9,342,907,469 bytes |
| Model config | SHA-256 `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670` |
| Dataset manifest provenance | SHA-256 `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED` |
| Dev payload | 64 synthetic rows, SHA-256 `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7` |
| Fitted candidate | Job `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-FIT-20260928-01`; manifest SHA-256 `D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E` |
| Fit resource log | SHA-256 `5812CD2BE242B407CBA8EFE8E04813D6973BCB2B9CD61A958849B491B7DFB781` |
| Fit epoch metrics | SHA-256 `889F5FCA08FAA5C5845BF2C8F2168A371F91108ADBFCAD55FE28B9D384AA765D` |
| Adapter weights | 6,300,864 bytes; SHA-256 `051A942CC306D15FF22AD300D6256CC4B8E6335B9C6263B65696353B04938E5C` |
| Adapter config | SHA-256 `F77ECF3C2E87B2586563F3CA6017B74F62B180C31F67260A590CCFF85453531F` |
| Adapter README | SHA-256 `D402F188EBE4AA2ABEB5929611EE4C919D4DAEE9B69751E499696F871F82DC96` |
| Trainer | SHA-256 `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5` |
| Training protocol | SHA-256 `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893` |
| Fit preflight manifest | SHA-256 `6EA37A8BA9A1B75CC1E4749085E7EB50E456BFAE039FAF6E74417EF3DCC353C4` |
| Fit preflight resources | SHA-256 `0629B827E4704445BF3E456B331A8C917C0B135460C019FA99C88D514A769732` |
| Pinned-tree helper | SHA-256 `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |

| Prepared projection | Exact identity |
|---|---|
| Projection helper | SHA-256 `92E90F2F323BAC9F917C06DE318FA3B4E89EC0FD5FC7DC00989E2A7EF3ED88B8` |
| Prompt-only JSONL | 60,203 bytes; SHA-256 `6BE3C1E65342711AF8FCB7C6F44ED53B5986D31AD93FE0C9EE1542E537268BAF` |
| Prompt manifest | 861 bytes; SHA-256 `DC4C3B605F7CC2AC62AA283BDD90B55FBCDA7CB4BF526441306EC25508167939` |
| Oracle-only JSONL | 14,612 bytes; SHA-256 `B6AC5D5C81A1390CC8A9A12D065E8C58CD62242A3308C754641424B1CF783701` |
| Oracle manifest | 853 bytes; SHA-256 `B23449AE7809432B1C5EAD7D915B7E8D635EF48FE882CBB7FBCDF8742E1C675E` |

The combined dev payload is transformed in a separate offline preparation
step by [`prepare_gateway_lora_screen_03_4b_dev.py`](../../../tools/prepare_gateway_lora_screen_03_4b_dev.py).
That helper is the only evaluation component that reads the combined labeled
source. It writes distinct prompt-only and oracle-only files and manifests
under the approved data root, each pinned by exact SHA-256, byte count, row
count, source identity, helper identity, and the active ITER169 reservation.
The scorer reads only the prompt file before generation. The model process
never loads or parses the combined source, family/group/task labels, or oracle
file until both prediction files have been flushed and sealed. Only then, in
full-score mode, it opens the oracle-only projection. Preflight never opens the
oracle projection. No held-out path is resolved, opened, hashed, or enumerated.

Before any directory or file is created, the helper and scorer check that all
planned output, log, and scratch paths are beneath `C:\wrench-slm-data` and
that extant ancestors are not symlinks, junctions, or reparse points. They
repeat these checks immediately before and after writes. These are cooperative
path checks, not a race-free filesystem sandbox: a concurrent actor able to
replace a path component between checking and opening could still create a
time-of-check/time-of-use race. Use only on the controlled local host with the
destination directories not concurrently modified. Any detected redirection,
existing one-shot output, cap breach, or reservation change fails closed.

## Runtime and execution limits

- Windows Python 3.13.15 at
  `C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe`.
- Exact package versions: Torch `2.14.0+cu132`, Transformers `5.17.0`, PEFT
  `0.21.0`, Accelerate `1.15.0`; verify the approved module origins.
- One NVIDIA GeForce RTX 5060 Ti, UUID
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. Use BF16, `cuda:0`, one request
  at a time. No CPU fallback.
- Hugging Face and Transformers offline flags are mandatory; model and adapter
  load from the pinned local paths with `local_files_only=True` and
  `trust_remote_code=False`. No package installation or download.
- Greedy decoding: `do_sample=False`, `num_beams=1`, max 96 generated tokens,
  Transformers `max_time=300` seconds. This setting is cooperative and is not
  a hard per-generation cancellation guarantee. The operator must supervise
  the process with an external hard job timeout of 900 seconds for preflight
  and 14,400 seconds for full scoring, then record forced termination as a
  failed attempt. Keep the exact tokenizer chat template from the completed
  fit receipt.
- Maintain at least 10% free system RAM and GPU VRAM. Start a one-second
  resource monitor before loading model packages and interrupt on a reserve,
  reservation, scratch, device-identity, or log-cap breach. Record every sample.
- Runtime scratch cap: 256 MiB for preflight; 512 MiB for full score. Resource
  logs and individual receipts/prediction files cap at 20 MiB. Combined
  evaluation outputs cap at 128 MiB. Each mode uses a fresh scratch directory
  and refuses existing output paths.
- Candidate is opened read-only and remains inactive. It cannot route, call a
  provider, use tools, mutate code, alter permissions, or change active model
  state.
- This package has no provider client and makes zero SubRoute or Frontier API
  calls. Token counts are from the local tokenizer. They are not API usage,
  billed tokens, or measured savings.

Before each one-shot job, obtain fresh storage status and a unique reservation:

```powershell
python tools/check_wrench_storage_budget.py status --include-root C:\wrench-slm-data
python tools/check_wrench_storage_budget.py reserve --job-id WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-NN --reserve-bytes 500000000 --include-root C:\wrench-slm-data
```

For full scoring use a fresh `WRENCH-QWEN35-4B-DEV-SCORE-20260929-NN` ID and
reserve at least `1000000000` bytes. `NN` must be replaced by an unused unique
suffix. Verify the active reservation and at least 5 GiB destination free
space beyond reserved writes. Include every current external Wrench path in
the storage scan. Keep actual data plus all active reservations strictly below
50,000,000,000 bytes. Release only after the process stops and output sizes and
hashes are accounted for.

Illustrative invocation after review and storage/resource admission:

```powershell
C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe tools\score_gateway_lora_screen_03_4b_dev.py --mode preflight --storage-reservation-job-id WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-NN
C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe tools\score_gateway_lora_screen_03_4b_dev.py --mode score-dev --storage-reservation-job-id WRENCH-QWEN35-4B-DEV-SCORE-20260929-NN --preflight-receipt C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-eval\preflight-WRENCH-QWEN35-4B-DEV-PREFLIGHT-20260929-NN\preflight.json
```

The one-prompt preflight is `PREFLIGHT_COMPLETED` only when both the base and
LoRA arm have no runtime error, no cooperative `max_time` overrun, elapsed time
below 300 seconds, a nonempty encoded prompt and generated completion below
the 96-token cap, nonempty output, and a valid output schema. Any violation
produces a `PREFLIGHT_FAILED` receipt containing both prediction-file hashes,
the per-arm failure codes, resource-log hash, and pinned input/runtime/device/
reservation identities. The process exits nonzero after sealing this receipt.
The raw base and LoRA prediction JSONL files remain beside the receipt.

Full scoring verifies both preflight prediction-file hashes and the exact
resource-log hash and samples, then inspects the sealed predictions. It rejects
any failed preflight status or error, cooperative timeout, elapsed-time
overrun, empty generation, token-cap hit, or invalid schema before opening the
prompt projection or loading the model into the inference runtime. It also
requires the same exact evaluator, protocol, base, tokenizer, fit receipt,
data, runtime, GPU, reservation, and resource identities. Keep the two
reservation IDs distinct. Any failed or interrupted attempt is diagnostic
evidence; do not reuse its ID or output path.

`max_time=300` remains cooperative. For an external 900-second preflight or
14,400-second full-score hard stop, the supervisor must wait for the process to
exit, then leave a `failure.json` receipt in that job's output directory with
the job ID, exact scorer/protocol hashes, time, and external-stop reason. Such
a receipt is an incomplete failed attempt, never `PREFLIGHT_COMPLETED`; do not
reuse that job ID or output directory. If the process is killed before it can
seal both arm files, record that fact in the supervisor receipt rather than
claiming both predictions were retained.

## Outcomes and interpretation

For each arm report the exact denominator, strict valid-schema rate, exact
oracle decision rate, route accuracy and counts, per-family outcomes,
timeouts, invalid or duplicate evidence IDs, authority-key violations,
generation-limit hits, failure examples, prompt/completion local-token counts,
mean and p95 latency, and the paired LoRA-minus-base exact-accuracy delta.
Exact oracle success requires valid output, no timeout or runtime error, and
exact equality with the frozen reference object. Report confidence intervals
with denominators; keep all failures in the aggregate. A missing arm or fewer
than 64 full-score rows is an incomplete run, never a pass.

The local token counts only describe the model input and generated output in
this offline diagnostic. A tokenizer is not a compressor that can send opaque
token IDs to arbitrary Frontier APIs. A real provider request generally sends
the provider's accepted text/message format and the provider determines its
own token usage. Frontier savings require a paired baseline and hybrid request
with provider-reported usage for every call, retry, verification, and recovery
step. This experiment makes no such requests and cannot estimate billed
savings from these local counts.

Even a perfect score is synthetic label agreement, not evidence of useful
software engineering. It does not establish the active goal's requirements:
95% verified task completion without Frontier calls, at most 5% Frontier-routed
episodes, at least 95% verified task-success retention, at least 95% fewer
Frontier tokens, at least 95% lower all-in cost, or reliable all-day work
across repositories, languages, tests, interruptions, recovery, and regression
handling. Those claims require a separate preregistered representative matched
task study, all-in accounting, confidence bounds, and sustained-use evidence.
