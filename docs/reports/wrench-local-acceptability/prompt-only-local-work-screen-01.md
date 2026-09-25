# Prompt-only local work screen 01

**Result: FAIL_DIAGNOSTIC.** All 18 generations completed, but no answerable
case met the exact answer, response-schema, and evidence oracle. The only
three whole-case passes were correct abstentions. No task class passed its
six-case rule, and no semantic local work is accepted by this screen.

## Decision

This run supports no user-facing or autonomous generative task envelope for
the tested local model. Keep training stopped: the work class that training
should improve has not passed a held-out, tool-backed outcome screen. Existing
deterministic exact-read, literal-search, and narrow patch-operation results
remain mechanics evidence for those operations; they do not turn the SLM's
generated answers into accepted work. Treat every generative output as
unverified until an external reviewer checks it.

The diagnostic used three short closed-form text classes: exception mapping,
unique configuration extraction, and function localization from a supplied
snippet. It used four answerable examples and two missing/ambiguous boundaries
per class. The model had no tools, file access, or mutation capability. The
fixture is exposed development material with a fixture-authored oracle, so
these counts are not a real-task acceptance rate or a held-out estimate.
The run cannot satisfy the broader local-model gate, which requires evidence
from an actual tool result.

## Results

| Class | Exact positive accepts | Correct boundary abstentions | Wrong boundary decisions | Invalid response schemas | Full class pass |
| --- | ---: | ---: | ---: | ---: | --- |
| Exception-to-category mapping | 0/4 | 2/2 | 0/2 | 4/6 | No, 2/6 whole cases passed |
| Unique configuration extraction | 0/4 | 1/2 | 1/2 | 5/6 | No, 1/6 whole cases passed |
| Function localization | 0/4 | 0/2 | 2/2 | 6/6 | No, 0/6 whole cases passed |
| **Total** | **0/12** | **3/6** | **3/6** | **15/18** | **No, 3/18 whole cases passed** |

The log cases cite the correct source line but return `TimeoutError`,
`PermissionError`, and similar exception names instead of the requested
normalized categories. They also put explanatory text in `reason`, where the
frozen schema requires `null`. Two log boundaries abstain exactly.

In configuration extraction, two answers contain the right value and a
grounded quote, but explanatory text in `reason` violates the exact schema.
Other positive responses omit quote fields or use a placeholder quote. The
model answers the ambiguous duplicate-key case instead of abstaining. It
correctly abstains on the missing-key case.

In function localization, each known response gives only the function
definition and omits the required property-access citation. One also names the
wrong function. Both missing/ambiguous cases are answered with guesses instead
of abstentions.

The receipt's `exact_answers` field counts exact unknown responses as well as
known answers; it should not be read as a count of positive accepts. Under the
frozen full oracle, positive accepts are 0/12 and the three exact unknown
responses are the only passes.

## Runtime and accounting

- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`.
- Host run: repository HEAD `8a0a71a5508b031da07ca1c4d8b9b57d17bf5000`;
  Python 3.13.15, Transformers 5.17.0, PyTorch 2.14.0+cu132, CUDA 13.2,
  Tokenizers 0.23.2, and verified 35-package lock SHA-256
  `0ed35342ae184741886fff2764f87c44df8babfde3912c54a9e1cd73ffbf2420`.
- Serializer: `direct_transformers.apply_chat_template.v1`; template SHA-256
  `273d8e0e683b885071fb17e08d71e5f2a5ddfb5309756181681de4f5a1822d80`.
  The pinned `tokenizer.json` SHA-256 is
  `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42`.
- Generation: greedy, one response per case, no retry, up to 192 new tokens.
  All 18 cases completed in 383.19 summed case seconds; mean case latency was
  21.29 seconds and the maximum was 33.67 seconds. Optional fused kernels
  were unavailable and the runtime used slower reference implementations.
- Local accounting: 4,957 prompt tokens and 733 completion tokens. These are
  local model tokens, not frontier usage or token savings.
- Resource minima: 43.19% RAM free and 83.97% VRAM free, above the required
  10% reserve. The final storage check was `WITHIN_LIMIT` at 10,113,586,125
  actual bytes plus 151,203,000 bytes in active reservations, below the 50 GB
  decimal cap.
- Provider calls: 0. Frontier matched usage pairs: 0. Frontier-token savings:
  `N/A`.
- Training, weight updates, client routing, and tools: none.

## Frozen evidence

The run followed the [preregistered protocol](../../evals/wrench-local-acceptability/prompt-only-local-work-screen-01-protocol.md).
The receipt is stored outside the repository under the approved Wrench data
root at
`C:\wrench-slm-data\artifacts\wrench-local-acceptability\prompt-only-work-01.json`.
Receipt SHA-256:
`20e8082c5e71c570902fef26e1c24091c6c29c283786a4fb548ab487e20e9868`.
Fixture SHA-256:
`525f8cb9639d17633a466129fb7b386ea0cdd33594e4c9a34e10dd6de40ecf9e`.

Independent static receipt reviews reconciled the fixture, case scores,
runtime pins, token totals, and resource reserve. They confirmed the diagnostic
failure and no identity or accounting mismatch.
