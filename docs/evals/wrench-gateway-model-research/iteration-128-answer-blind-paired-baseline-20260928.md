# Iteration 128: answer-blind paired local-context baseline

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-LOCAL-CONTEXT-ITER128`  
Status: **first answer-blind paired run; 94.9153% local input-token reduction; verifier formatting needs correction**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Answer-blind paired task result

Following Iteration 127's prompt-leak audit, none of the three questions or
the system instruction contained the expected answer. The runner checks this
before loading the model and records each question hash. The same pinned
Qwen3.5-0.8B base model answered the full-fixture and E0 budget-64 prompts for
each frozen synthetic task.

| Task | Full-context input | E0 input | Raw full / E0 output |
|---|---:|---:|---|
| Retry policy | 8,738 | 545 | `250, 4000` / `3, 250` |
| Session lifetime | 8,731 | 437 | `1800, 300` / `1800,300` |
| Retry function | 8,727 | 350 | `calculate_retry_delay` / `calculate_retry_delay` |
| **Total** | **26,196** | **1,332** | **30 / 26 output tokens** |

On the local model tokenizer, input reduction was **94.915254%**. Counting
generated output too, the reduction was **94.821932%** (26,226 to 1,358 total
tokens). The target tokenizer measured 19,297 to 1,626 prompt-input tokens,
or **91.573820%**. These are local prompt measurements; frontier-token savings
remains null because no frontier-only call was made.

The receipt's initial exact-string verifier counted full-context 1/3 and E0
2/3. Inspection shows the numeric-answer prompts request two comma-separated
integers but do not prohibit spaces: `1800, 300` and `3, 250` are valid pairs.
The byte-exact verifier incorrectly rejects those values. The retry-policy
full-context output `250, 4000` is genuinely wrong for the requested order and
fields; E0's `3, 250` is correct under the stated format. Until a
format-aware, deterministic verifier is run on both arms, use the receipt's
raw outputs and token counts, not its exact-string success booleans, as the
authoritative evidence. This is a verifier-definition defect, distinct from
the answer leak in earlier iterations.

## Identity and runtime

- Prompt profile: `answer_blind_lookup_v1`; expected-answer leakage check was
  false for all three questions.
- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16, no adapter; context budget
  64.
- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Runner SHA-256:
  `4af2713254682a25f6c55e7ce0a11e881bea78c45aaf383ea40f7af901dad83d`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter128.json`,
  5,642 bytes, SHA-256
  `15fb410f2f192a488d1085956bbb6bcfb0ad223998a53b6afe9350307185075d`.
- Model load 4.6612 s; total 41.753 s. Peak CUDA allocated/reserved:
  2,678,108,160 / 2,894,069,760 bytes. Minimum free RAM 14.348%; minimum
  free VRAM 75.3908%; 31 samples, telemetry valid. The 10% runtime floor held;
  Fit-03's 25% RAM start condition did not.
- Storage reserved 100,000,000 bytes, included the Docker WSL model volume
  and hourly automation directory, and remained within 50 GB. C: had over
  139 GB free. No provider call or spend occurred.

## Next action

Implement a task-specific format-aware verifier: accept whitespace around the
comma for the two integer pairs, keep the function-name check exact, and apply
the same rules to both arms. Re-run the same answer-blind episode set at
budget 64 before claiming completion retention. Then continue the budget
search between 60 and 64; the 95% token target remains unproven.
