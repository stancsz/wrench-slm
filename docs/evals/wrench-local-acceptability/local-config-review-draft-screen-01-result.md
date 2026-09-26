# Local config review draft screen 01 result

- Job: `W2-LOCAL-SLM-CONFIG-DRAFT-RUN-20260925`
- Run date: 2026-09-26
- Model: `Qwen/Qwen3.5-0.8B` at revision `2fc06364715b967f1860aea9cf38778875588b17`
- Runtime: Python 3.13.15, Transformers 5.17.0, Tokenizers 0.23.2, PyTorch 2.14.0+cu132
- Serializer: `direct_transformers.apply_chat_template.v1`
- Outcome: stopped after first scored failure and second generation/runtime failure
- Frontier calls and matched usage pairs: 0
- Average frontier-token savings: **N/A**

## Observed result

The screen loaded the pinned local model and attempted two of the twelve authored
synthetic configuration review cases. It stopped after the second case failed
JSON validation. No case passed, ten cases were not run, and no prohibited tool
attempts were recorded.

| Case | Class | Result | Input tokens | Output tokens | Generation time | Finding |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `positive-relay-port` | positive | Completed, incorrect | 322 | 75 | 33.79 s | Returned `listen_port=8080` unchanged and skipped the required read/evidence flow. |
| `positive-worker-retry` | positive | Failed | 322 | 65 | 26.88 s | Generation ended with `ChallengeError:invalid_json`; no parseable answer was recorded. |

Total measured local usage was 644 input tokens, 140 output tokens, and 784
combined tokens. The generation times sum to 60.67 seconds; case wall times
were 34.26 and 27.13 seconds. These local model token counts are not a measure
of frontier-token savings.

Resource telemetry recorded minimum free RAM of 47.1% during model load and
minimum free VRAM of 83.1% after load. Storage remained below the 50 GB limit.
There was no repository file application, training, tuning, retry, fallback,
client/provider call, or real task capture. Python socket connection methods
were blocked and Hugging Face ran offline/local-only; the process did not have
OS-level network isolation.

## Interpretation

This configuration-review workflow is **not acceptable locally with this
model/harness identity as measured**: the first requested edit was wrong and
ungrounded, and the next answer was not valid JSON. The result supports
prioritizing response-format reliability and read-before-edit grounding before
spending effort on training. It says nothing about other kinds of work because
the diagnostic stopped after two cases and used a small authored fixture.

The run does not establish production utility, a representative task success
rate, or any token savings. No matched frontier tasks were collected. A future
frontier savings estimate needs authorized paired tasks, an independent
outcome oracle, and complete input/output ledgers for direct and Wrench-assisted
arms, including retries, verification, repairs, rebuilds, failures, and
fallbacks.

## Evidence

The full receipt is retained outside the repository at
`C:\wrench-slm-data\\artifacts\\wrench-local-acceptability\\local-config-review-draft-screen-01.json`
(SHA-256
`1530B61F67E72F57D3A5A2C546F743FEA014C5857B780BD31F6A96C01021EFB2`). The
stdout log is empty. The bounded stderr log, including model-load progress and
kernel fallback notices, is retained at
`C:\wrench-slm-data\\logs\\wrench-local-acceptability\\local-config-review-draft-screen-01.stderr.log`
(1,792 bytes, SHA-256
`3A2E702151B8386E8FCA6F55395249555F3E000F3B6B7E8BD3CFEA0B1E9532D8`).

See the frozen [screen protocol](local-config-review-draft-screen-01-protocol.md)
and [preparation report](../../reports/wrench-local-acceptability/local-slm-config-draft-prep-20260925.md)
for fixture semantics, guards, and pre-run verification.
