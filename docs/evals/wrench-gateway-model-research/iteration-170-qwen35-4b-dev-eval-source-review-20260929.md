# Iteration 170: Qwen3.5-4B dev evaluator independent source review

Review assignment: `WRENCH-QWEN35-4B-DEV-EVAL-REVIEW-ITER170-20260929`  
Nonce: `20a40df3-3fd2-4c56-a11a-460199011823`  
Expected repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Verdict

**FAIL for execution admission; source repair required.** This static review
found a blocker in the preflight success gate. No inference or scoring is
authorized by this review.

The scorer catches per-arm generation exceptions and records them in each
prediction row, but then unconditionally writes `PREFLIGHT_COMPLETED` after
the loop when the process and resource monitor finish. The `score-dev` path
checks that status plus receipt and file hashes, but does not inspect the
preflight prediction rows to require successful, non-timeout output from both
arms. Therefore a preflight with a model error or cooperative time-budget
exceedance can be admitted to full scoring as a completed preflight. The
protocol calls for a successful matching preflight, so its present status is
not sufficient evidence.

Repair the scorer so the preflight result cannot have a successful status
when either arm errored or exceeded its generation budget, and make
`score-dev` verify those conditions from the hash-bound preflight prediction
files before loading the model or dev prompts. Preserve failed attempts as
failures, not reusable successful preflight receipts. Then request a fresh
static review of the changed source and protocol identities.

## Scope and method

Read only the assigned evaluator, projection helper, protocol, repair report,
their exact pinned prompt/oracle projections and manifests, and the specified
repository identity. I did not read the combined dev payload or any held-out
payload, and I do not reproduce oracle values here. I ran no Python, parser,
AST check, test, helper, tokenizer, model/runtime import, inference, benchmark,
training, network request, provider/SubRoute call, or credential access. No
files other than this review report were written.

The review checked: prompt-only data is the sole input supplied to model
generation; predictions for both arms are flushed and hashed before the
oracle projection is loaded; adapter-disabled and adapter-enabled arms share
the same model/tokenizer and prompts; model, training, runtime, GPU, fit,
reservation, preflight, and projection identities are pinned; output and
scratch paths are confined under the approved data root with reparse checks;
timeouts are described as cooperative with an external job timeout; and
failures, denominators, confidence intervals, and local-token-count limits
are represented in the scoring receipt.

## Identity verification

Repository HEAD was `af01304824f079a64b6c3902397a2034b843511a`.

| Assigned identity | SHA-256 observed |
|---|---|
| `tools/score_gateway_lora_screen_03_4b_dev.py` | `233426CFFF1E5DBF479BEC0256A0DDB79896D6E3A3FAB47DADD6EA890C2052C9` |
| Actual helper path `tools/prepare_gateway_lora_screen_03_4b_dev.py` | `92E90F2F323BAC9F917C06DE318FA3B4E89EC0FD5FC7DC00989E2A7EF3ED88B8` |
| `docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md` | `079B17BC7848E85AC9B1764864F78C2D7AF911150517EFEF12FAAE87E9A3F341` |
| `docs/evals/wrench-gateway-model-research/iteration-169-qwen35-4b-dev-eval-source-repair-20260929.md` | `3FF231214AD5D263DAF53263E9EDC028A1D11DC628DB23718526E11BD3DF8F7F` |
| Prompt projection | `6BE3C1E65342711AF8FCB7C6F44ED53B5986D31AD93FE0C9EE1542E537268BAF` |
| Prompt manifest | `DC4C3B605F7CC2AC62AA283BDD90B55FBCDA7CB4BF526441306EC25508167939` |
| Oracle projection | `B6AC5D5C81A1390CC8A9A12D065E8C58CD62242A3308C754641424B1CF783701` |
| Oracle manifest | `B23449AE7809432B1C5EAD7D915B7E8D635EF48FE882CBB7FBCDF8742E1C675E` |

The assignment named the helper as `prepare_gateway_lora_screen_03_4b_dev_split.py`
and projections under `C:\wrench-slm-data\datasets\...`. Those paths do not
exist. The protocol, scorer, repair report, and supplied hashes identify the
actual helper as `prepare_gateway_lora_screen_03_4b_dev.py` and the actual
projections under
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-projections-iter169\`.
The actual files at those locations match all supplied hashes. This path
label discrepancy did not change the reviewed source identity.

## Findings

| Area | Result |
|---|---|
| Prompt/reference separation | Pass by static inspection. The scorer loads prompt-only rows first, gives only system/user messages to generation, seals and hashes both arm prediction files, then loads the oracle projection for `score-dev`. Preflight does not open oracle data. |
| Held-out isolation | Pass within reviewed source. No held-out path is used or resolved. |
| Fit and model binding | Pass by static inspection. The code verifies pinned fit manifest/resources/epochs, adapter files, base inventory/config, training source/protocol, and local runtime/GPU identities. |
| Arm pairing | Pass by static inspection. Both arms use the same loaded adapter-wrapped model and tokenizer; the base arm enters `disable_adapter()`, and the LoRA arm uses the enabled adapter on identical prompts. |
| Resource and output controls | Conditional. Reservation, 5 GiB destination headroom, output/scratch caps, resource monitor, 10% RAM/VRAM checks, and reparse-point checks are present. The source and protocol correctly disclose that ordinary path checks have a TOCTOU race and that `max_time` is cooperative. An external supervisor still must enforce the documented wall-clock limit and record forced termination as failure. |
| Preflight success semantics | **Fail.** Errors and generation-budget exceedances are serialized but do not prevent `PREFLIGHT_COMPLETED`; `score-dev` validates hashes but not successful preflight predictions. |
| Effectiveness scope | Correctly limited. The protocol labels the local tokenizer counts as non-provider counts and disclaims engineering utility, frontier savings, cost savings, held-out performance, and product acceptance. |

Scoring denominators are explicit (`n`, 64 dev rows), exact and schema rates
include Wilson intervals, and route/family counts, timeout/error/invalid
output counts, failures, local-tokenizer counts, and paired differences are
reported. These do not cure the preflight admission blocker.

## Commands and resource sample

Read-only commands used:

```powershell
git rev-parse HEAD
Get-Date -AsUTC -Format o
Get-FileHash -Algorithm SHA256 <the eight exact source/projection files listed above>
Get-Content <assigned source/protocol/report files> -TotalCount <bounded range>
Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.free --format=csv,noheader,nounits
git status --short --untracked-files=no
```

At the last sample, system RAM free was 25.53% (8,549,728 KiB of
33,486,624 KiB); GPU 0 was the pinned RTX 5060 Ti, with 15,208 of 16,311
MiB free. No workload was started. These values are a point-in-time review
sample, not admission for a later run.

The assigned 25,000-byte storage reservation was already admitted by the
parent task. I did not start a workload or alter/release that reservation.

## Limits

This is a static source review, not a runtime verification. It does not prove
the model loads, that the split helper output is semantically correct beyond
the pinned hashes and inspected transformation, or that any task-quality,
compression, savings, cost, all-day reliability, or product-acceptance target
is met. The fitted candidate remains inactive.
