# Iteration 172: Qwen3.5-4B dev preflight gate review

Assignment: `WRENCH-QWEN35-4B-DEV-EVAL-REVIEW-ITER172-20260929`  
Nonce: `04b2e1e8-4a7d-42c4-a5dc-d2585e421b12`  
Expected HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Verdict

**PASS for the Iteration 170 preflight-gate source repair.** The previously
identified failure path is closed by the reviewed source. This static review
does not authorize execution; fresh storage and resource admission and the
documented external timeout supervision remain required.

The scorer now evaluates both sealed preflight arm rows with a shared success
predicate. It requires no generation error or cooperative time overrun,
elapsed generation time below 300 seconds, a nonempty encoded prompt and
completion, fewer than 96 completion tokens, nonempty text, and valid output
schema. Any issue is included in `preflight_failures`, changes the status to
`PREFLIGHT_FAILED`, and causes a nonzero exit after the failed receipt is
written. Full-score admission verifies the prediction hashes, parses exactly
one row per arm, requires the same recorded example ID, re-applies the
success predicate, and rejects any non-completed status or failure before it
loads the prompt projection or model runtime. The Iteration 170 blocker is
closed.

## Review scope

Reviewed the changed scorer and protocol, Iteration 171 repair report, prior
Iteration 170 review, and the exact unchanged helper and prompt/oracle
projection identities. Checked the relevant preflight gate, sealed prediction
reader, generation success predicate, model/prompt load order, resource
receipt validation, prompt/oracle ordering, and offline/no-activation
boundaries. No combined dev or held-out payload was read, and no oracle values
are reproduced here.

No Python, AST or syntax check, test, projection helper, tokenizer, model or
runtime import, inference, benchmark, training, network/provider/SubRoute
request, credential access, or held-out access was performed. No files other
than this report were written.

## Verified identities

HEAD was `af01304824f079a64b6c3902397a2034b843511a` both before and after the
review.

| File or input | SHA-256 |
|---|---|
| `tools/score_gateway_lora_screen_03_4b_dev.py` | `14EC4C0939E8135A14D31A9A93E51DE6DF01DA658E6F42A3369967E94C4C2D05` |
| `tools/prepare_gateway_lora_screen_03_4b_dev.py` | `92E90F2F323BAC9F917C06DE318FA3B4E89EC0FD5FC7DC00989E2A7EF3ED88B8` |
| `docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md` | `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6` |
| `docs/evals/wrench-gateway-model-research/iteration-171-qwen35-4b-dev-eval-failure-repair-20260929.md` | `BD47EF83B114D2335D85BDE5E3635C7BD6DAB07021FC555F4E33792D648C9D8D` |
| Prior review, Iteration 170 | `E05E336C60BC7BA42D39A6664B3784DFED60FBCFF8E42B7FA281CDFE5FA8F2CB` |
| Prompt projection | `6BE3C1E65342711AF8FCB7C6F44ED53B5986D31AD93FE0C9EE1542E537268BAF` |
| Prompt manifest | `DC4C3B605F7CC2AC62AA283BDD90B55FBCDA7CB4BF526441306EC25508167939` |
| Oracle projection | `B6AC5D5C81A1390CC8A9A12D065E8C58CD62242A3308C754641424B1CF783701` |
| Oracle manifest | `B23449AE7809432B1C5EAD7D915B7E8D635EF48FE882CBB7FBCDF8742E1C675E` |

The projection files are in
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-projections-iter169\`.
These hashes match the assigned identities.

## Remaining limits and conditions

- The 300-second Transformers `max_time` remains cooperative. The protocol
  specifies an external 900-second preflight and 14,400-second full-score
  hard timeout, with a failure receipt if the supervisor stops a job. This
  supervisor is an operational prerequisite, not a capability implemented by
  the scorer.
- Output-path checks disclose a time-of-check/time-of-use race if another
  process replaces path components concurrently. Run only with controlled
  destination directories as stated in the protocol.
- The experiment is a synthetic 64-row dev diagnostic. It cannot demonstrate
  representative coding performance, provider-billed token savings, cost
  savings, all-day reliability, held-out performance, or the product's 95/5
  acceptance targets. Local tokenizer counts are explicitly not Frontier
  usage. The adapter remains inactive.

## Commands and point-in-time resources

Read-only commands used:

```powershell
git rev-parse HEAD
Get-Date -AsUTC -Format o
Get-FileHash -Algorithm SHA256 <the nine assigned source, report and projection files>
Get-Content <bounded scorer, protocol and report sections>
Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize
nvidia-smi --query-gpu=index,uuid,name,memory.total,memory.free --format=csv,noheader,nounits
```

At the last sample, system RAM free was 24.31% (8,139,820 KiB of 33,486,624
KiB). GPU 0 was the pinned RTX 5060 Ti, with 15,200 of 16,311 MiB free. No
workload was started. These readings are not a later-job admission.

The task owner had already admitted a 25,000-byte review reservation. I did
not create, change, or release it.
