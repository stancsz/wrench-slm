# Iteration 196: Frontier response-usage accounting contract

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Disposition: **PASS for the bounded synthetic accounting contract only.**

## Change

Added `src/wrench_harness/frontier_usage.py` to parse OpenAI-compatible chat
response usage fields without retaining response text, then aggregate provider
response-reported prompt and completion tokens across paired baseline/Wrench
episodes. The contract counts every captured retry, records cached input as a
subset (it does not add cached tokens a second time), permits a Wrench episode
with zero Frontier requests, and rejects missing usage, malformed counts,
unpaired episodes, incomplete captures, non-contiguous attempts, and tampered
receipt fields.

The receipt hash binds its local identities and parsed counts to a digest of the
raw response body. It is not a signature and does not prove who produced the
response. `provider_route` is caller-supplied metadata. The aggregate explicitly
marks response usage as not billing-verified.

## Verification

Ran the six synthetic unit cases in `tests/test_frontier_usage.py` with:

```powershell
$env:PYTHONPATH='src'; py -3.13 -m unittest discover -s tests -p 'test_frontier_usage.py' -v
```

Result: **6 passed**. The configured project virtual environment and global
Python 3.13 do not have `pytest` installed, so the requested focused test file
was run with Python's built-in `unittest` runner. `git diff --check` completed;
Git printed existing working-tree line-ending warnings for unrelated files.

The assigned storage reservation was `WRENCH-GW-USAGE-RECEIPT-CONTRACT-20260929-01`
for 100,000,000 bytes, admitted while total Wrench storage was `WITHIN_LIMIT`.
The run used synthetic in-memory response bodies only. No API, provider,
SubRoute, credentials, or held-out data were accessed. The concurrent Qwen3.5-4B
local development score remained above the 10% RAM/VRAM free floor while these
small tests ran.

## Exact identities

| File | SHA-256 |
|---|---|
| `src/wrench_harness/frontier_usage.py` | `3E7642CA7141F0A1B3AC0B5EF54B62E00D070BA4A6289FC4992AB8624F17D374` |
| `tests/test_frontier_usage.py` | `51E38A75A7C780713ADA69EEACE4F38A1FCADEA6F2DE8F5DA916348FF12D2C33` |

## Limits and next step

This module is not yet wired to OpenCode or SubRoute response transport. It
supports the OpenAI-compatible Chat Completions usage shape only; other provider
schemas need separately pinned parsers. It cannot verify the actual upstream
provider identity, whether a proxy changed usage fields, billing, cost, task
success, local completion, or the 5% routing ceiling. Missing or unpaired real
usage remains unmeasured, not zero. The synthetic 95% example in the test is
only arithmetic validation, not product evidence.

Next, add the response-side capture at the actual bounded gateway transport and
bind each response receipt to its request and frozen task outcome. Keep upstream
traffic disabled until the campaign spend cap and route authority are available.
Then measure paired frontier-only and hybrid episodes from actual upstream usage
receipts, including retries, and report task-success and all-in cost separately.
