# Synthetic context token reduction screen 01

Status: **FAIL**, with partial positive evidence-selection results. This is an
open-development synthetic measurement, not a semantic SLM or frontier-usage
result.

## Frozen identities

- Protocol: [protocol 06](synthetic-context-token-reduction-protocol-06.md)
- Job ID: `W2-SYN-M3-CTX-REDUCTION-20260925-05`
- Nonce: `SYNCTX07-D8F4`
- Source revision: `b26418be3e398a396c8ee660bd032e7aac8771c5`
- Runner SHA-256: `84bc138a8948e7c69b03b3e999d1c9ce886116af321d22a4642da5ffc46a9d3d`
- Tokenizer: `MiniMaxAI/MiniMax-M3@f0e1c1e04d40177e4673a22097036854f536e9c0`
- Receipt: `C:\wrench-slm-data\artifacts\wrench-local-acceptability\synthetic-context-m3-reduction-05.json`
- Receipt SHA-256: `68d66186f4a78c4d6f577950b9256c285f8f41bfe8627ea7aba78565eb8fd870`

## Results

The seven exposed positive cases measured complete M3 chat-template input
tokens for a full-source baseline and the actual E0-prepared context. Five
passed the required source-evidence gate; two function-location cases did not.
The screen therefore returns **FAIL**. Four of four abstention boundaries
passed, including missing, stale, ambiguous, and insufficient-context-budget
cases.

| Case | Class | Baseline tokens | Wrench tokens | Reduction | Evidence gate |
| --- | --- | ---: | ---: | ---: | --- |
| `loc-a` | Function location | 620 | 599 | Excluded | Fail, required answer evidence incomplete |
| `loc-b` | Function location | 621 | 593 | Excluded | Fail, required answer evidence incomplete |
| `triage-a` | Log error type | 687 | 542 | 21.11% | Pass |
| `triage-b` | Log error type | 692 | 541 | 21.82% | Pass |
| `context-a` | Exhaustive literal search | 609 | 595 | 2.30% | Pass |
| `context-b` | Exhaustive literal search | 617 | 603 | 2.27% | Pass |
| `evidence-specific` | Exact config value | 599 | 535 | 10.68% | Pass |

Across the five eligible cases, the arithmetic mean is **11.64%**. The
ratio-of-sums is **12.11%**, from 3,204 baseline tokens and 2,816 Wrench
tokens. The two excluded function-location pairs do not contribute to either
metric. Their shorter Wrench prompts are not counted as savings because the
screen did not verify the required source evidence.

This supports a narrow next-work envelope for deterministic context selection
on these exposed fixtures: log-line triage, exhaustive literal search, and an
exact configuration read passed their evidence checks. The two function
location cases failed the same required-answer-evidence check and need an
independent diagnosis before that task shape can be considered. These outcomes
do not establish generated-answer correctness or local model task acceptance.

## Limits and disposition

- No model weights were loaded and no inference, provider call, client request,
  or localhost request was made.
- `frontier_token_savings_percent` is null; eligible frontier usage pairs and
  frontier calls are both zero. The 11.64% and 12.11% figures are synthetic M3
  tokenizer input reductions only.
- The cases were exposed development fixtures. Do not tune or train on them,
  and do not include them in utility, customer, or production metrics.
- Keep the acceptance status at **FAIL** until a fresh, reviewed screen passes
  all positive evidence gates. Training remains stopped.

Earlier one-shot attempts remain recorded in protocols 02 through 05. They do
not contribute positive savings results; protocol 06 and the receipt above
define the valid measurement.
