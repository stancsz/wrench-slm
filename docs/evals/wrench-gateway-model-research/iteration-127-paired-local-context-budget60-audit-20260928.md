# Iteration 127: paired local context at budget 60 and prompt audit

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-LOCAL-CONTEXT-ITER127`  
Status: **full-context 3/3; E0 2/3 prepared; paired all-case savings undefined; answer-exposure flaw identified**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Budget-60 run

At context budget 60, the full-fixture local-model arm answered all three
cases. E0 prepared two cases, both with required quotes visible and exact
answers; it abstained on `retry-function` because required evidence would be
omitted. The receipt correctly leaves the pooled paired reduction undefined.

| Case | Full-context input | E0 input | Outcome |
|---|---:|---:|---|
| Retry policy | 8,751 | 564 | Both returned `3,250` |
| Session lifetime | 8,754 | 460 | Both returned `1800,300` |
| Retry function | 8,739 | Not prepared | E0 abstained: `required_evidence_omitted` |
| **Total** | **26,244** | **1,024 on 2/3 only** | **Full 3/3; E0 2/3; all-case savings null** |

The first two paired cases used 1,024 versus 17,505 input tokens, a partial
94.15% reduction. It is not an all-case result. Budget 56 had the same
2-of-3 E0 coverage. At budget 64, all three E0 contexts passed and Iteration
125 measured a 94.7264% local-model input reduction, but the following audit
changes how those answer outcomes may be interpreted.

## Prompt-leak audit

All three prompts in the tested runner stated the expected answer directly,
for example, “Reply exactly `3,250`” and “Reply exactly `1800,300`.” The local
model could copy the answer without retrieving or interpreting the repository
evidence. This contamination invalidates the prior 0.8B exact-answer rates as
independent task-quality evidence, including Iterations 117, 119, 121, 125,
126, and this Iteration 127. Preserve those receipts, but do not use their
3/3 or 2/3 exact-string passes as proof of model retrieval capability,
frontier success retention, or product completion.

The paired token counts remain measurements of the tested strings on their
named tokenizers. They do not become frontier-token savings, and they do not
show what a model can accomplish when the answer is absent from the prompt.
The next run must use answer-blind questions, retain the exact same frozen
fixture, and verify outputs against labels that are never included in the
question or instruction.

## Identity, resources, and accounting

- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16, no adapter; context budget
  60.
- Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Runner SHA-256:
  `e55b3518d942f886d7febf00bd44231b694f143c404369157e18832ae483102d`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter127.json`,
  5,301 bytes, SHA-256
  `d16018eac3ff6ed613cc0047cfa7ebc6a39d37e3673a88d60ec2d054fb871084`.
- In-process minimum free RAM 13.874%; minimum free VRAM 75.1456%; 28
  samples, telemetry valid. The 10% runtime floor held; Fit-03's 25% RAM
  admission did not.
- Storage reserved 100,000,000 bytes, including the Docker WSL model volume
  and hourly automation directory; C: had over 139 GB free. The run exited,
  outputs were counted, and its reservation was released.
- No adapter training, provider request, or spend occurred.

The next paired evaluation corrects this validity issue before further savings
optimization. The full product thresholds and eight-hour engineering target
remain unproven.
