# Iteration 130: answer-blind budget-63 abstention

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-LOCAL-CONTEXT-ITER130`  
Status: **complete; E0 abstained on one of three tasks; all-case savings undefined**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Result

Using the same answer-blind tasks, Qwen3.5-0.8B revision
`2fc06364715b967f1860aea9cf38778875588b17`, and Iteration 129's
`answer_blind_lookup_format_v2` verifier, context budget 63 prepared only two
of three E0 cases. It failed closed for `retry-function` because the prepared
context would omit required evidence. The two prepared cases were correct;
the full-context arm also passed those two and failed `retry-policy`.

| Case | Full-context | E0 budget 63 | E0 input tokens |
|---|---|---|---:|
| Retry policy | failed (`250, 4000`) | passed (`3, 250`) | 558 |
| Session lifetime | passed (`1800, 300`) | passed (`1800,300`) | 440 |
| Retry function | passed (`calculate_retry_delay`) | abstained: required evidence omitted | n/a |
| **Coverage** | **3/3, 2/3 correct** | **2/3 prepared and correct** | **998 over prepared cases only** |

Because an episode abstained, the paired all-case local-token savings ratio is
**undefined**. Do not extrapolate the 998-token partial numerator. The
budget-64 Iteration 129 run is the lowest currently measured budget that
prepared all three cases; its 94.823637% local-model input reduction is still
below 95%, and is not frontier-token savings. The single budget step from 64
to 63 crosses a required-evidence boundary on this fixture.

## Identity and accounting

- Verifier: `answer_blind_lookup_format_v2`; all expected answers absent from
  questions and system prompt.
- Runner SHA-256:
  `4b715627b0cb566b06b889cb768f863702b0b7f91b2c83a78fdb10eff5242c27`.
- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Receipt:
  `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter130.json`,
  6,102 bytes, SHA-256
  `3c2592461ef567178da483771507d2c252baa36806eb006af7fb221d80891972`.
- The 10% runtime reserve held: minimum free RAM 13.8785%, minimum free
  VRAM 75.3050%; peak CUDA allocated/reserved was 2,678,108,160 /
  2,894,069,760 bytes. Model load took 5.1483 seconds; total run took
  41.8927 seconds. Reference implementations were used because
  `causal-conv1d` and `flash-linear-attention` were unavailable.
- Storage admission was `WITHIN_LIMIT`, including the Docker WSL model volume
  and hourly automation directory. No provider request, spend, adapter load,
  training, or held-out access occurred.

## Next action

Keep budget 64 as the current complete-coverage baseline. Improve the
deterministic prompt/context compiler only where a paired receipt can show
lower full-lifecycle input without losing required evidence; keep explicit
abstention and recovery accounting. Then resume the representative code-task
MVP and compare the shortlisted model sizes. This fixture does not demonstrate
open-ended coding, LoRA benefit, 95/5 routing, frontier savings, cost savings,
or day-long engineering.
