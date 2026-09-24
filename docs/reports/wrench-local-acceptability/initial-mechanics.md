# Initial local acceptability measurement

Date: 2026-09-24 (America/Edmonton)

## Result

The provider-free deterministic rule route matched the frozen mechanics and
answer oracles on all **10/10 authored synthetic cases**. This is a narrow
local mechanics result. It does not measure an SLM, real coding tasks, or
frontier-token savings.

| Task class | Cases | Correct fixture outcomes | What the result covers |
| --- | ---: | ---: | --- |
| Exact function localization | 2 | 2 | Name the function containing a requested attribute and cite its line |
| Log error extraction | 2 | 2 | Report the frozen error type and log line; not root-cause diagnosis |
| Literal context selection | 2 | 2 | Select exact literal matches, account for a distractor, and return a valid empty result for a no-hit case |
| Missing or stale evidence | 2 | 2 correct abstentions | Return unknown without evidence when a requested source is absent or changed after snapshot |
| Ambiguous or specific source | 2 | 1 correct abstention, 1 correct accept | Abstain on a vague source request; extract a known config value from an exact path |
| **Total** | **10** | **7 completed, 3 abstained** | All outcomes are synthetic fixture mechanics |

The exact fixture manifest is
`tests/fixtures/e0_synthetic_matched_tasks_v1/manifest.json`, schema
`wrench.synthetic-matched-tasks.v2`, SHA-256
`871814333d9f582df9595ec486eb59fbf5f66c397cb451f6b67d9519d2bb72c5`.
It is Wrench-authored, open-development-only, non-sealed, and non-final. Its
admission permits fixture mechanics, not training or utility claims.

## How it was measured

Ran the eight focused functions in
`tests/test_e0_synthetic_matched_tasks.py` directly with the repository's
`.venv` Python 3. The behavioral checks invoked the actual bounded
`run_e0_rule_route` implementation over temporary copies of each case under
`C:\\wrench-slm-data\\tmp\\W2-NS-LOCAL-MECHANICS-REPLAY-20260924` and compared
its derived output with the independent frozen answer oracle. An earlier
exploratory invocation used Python's default system temp directory; its
temporary directories were removed automatically before this approved-root
replay. No test artifacts remain in that external temp location. The
suite also checked fixture identity/admission, paired boundaries, and that
missing, stale, and ambiguous evidence abstain. All eight functions passed.

`python -m pytest` was attempted with both the system Python 3.13 and repository
Python; neither has `pytest` installed. No dependency was installed. No model
inference, client prompt, provider call, network request, or training occurred.
This was a correctness check, not a latency or throughput benchmark.

## What is acceptable locally today

For the existing no-model route, accept only a small, bounded request that can
be answered from the supplied, validated snapshot by exact read, line read, or
literal search. A result must retain its source evidence. Use safe abstention
for missing, stale, ambiguous, unsupported, or insufficient evidence.

This evidence does not support local acceptance of code edits, test fixes,
semantic root-cause diagnosis, broad repository summaries, or ambiguous
requests. Those task classes need an identified local model and runtime plus a
held-out, task-specific oracle; real-work claims also need approved consented
tasks and a paired downstream baseline.

## Token and cost status

**Measured frontier-token savings: not established.** There was no model or
frontier request in this run, and the fixture tokenizer is not runtime-matched.
The result is not a measured 0% saving. For a future paired run, use
`1 - (all Wrench-workflow frontier tokens / all baseline frontier tokens)`
with complete call accounting and the same token usage convention on both
arms. Report local tokens, compute, latency, and amortized learning cost
separately.

## Environment gate

On this inspection, `C:\wrench-slm-data\weights` and `checkpoints` were
absent; no model weights were found in the inspected artifacts/cache paths.
The metadata-only Qwen candidate pins revision
`2fc06364715b967f1860aea9cf38778875588b17` and describes a 1,769,980,465-byte
repository snapshot, but this is not a local download or verified shard
inventory. The RTX 5060 Ti had 15,569 MiB free of 16,311 MiB and system RAM had
about 16.9 GiB free of 31.9 GiB. Hardware headroom does not remedy the absent
model/runtime identity.

The OpenCode profile targets `http://127.0.0.1:4000/v1`, but the latest
read-only route audit reported the gateway in forced OpenRouter mode. A local
endpoint is not evidence of local inference. Do not use it for a local SLM
measurement until its effective route is confirmed local without sending a
prompt.

## Decision

Continue measuring bounded no-model mechanics while preparing the exact
identity and consent gates. Do not train to discover which tasks matter. The
first local-model measurement should reuse these task classes only as an
open-development mechanics challenge; real acceptability must be decided on a
separate consented, outcome-verified pilot.
