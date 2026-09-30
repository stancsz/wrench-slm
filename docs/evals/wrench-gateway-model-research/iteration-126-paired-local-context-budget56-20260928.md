# Iteration 126: paired local context at budget 56

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-PAIRED-LOCAL-CONTEXT-ITER126`  
Status: **full-context 3/3; Wrench E0 prepared and verified only 2/3, abstaining on required evidence for the third**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Result

This paired run used the same fixture, three tasks, pinned Qwen3.5-0.8B base
model, runtime, and verifier as Iteration 125, with E0 context budget reduced
from 64 to 56. All three full-context baseline answers passed. E0 prepared two
cases, both of which retained their required quotes and passed the local-model
verifier. For `retry-function`, Wrench rejected the prepared prompt because it
would omit required evidence; the model was not called on that E0 arm. The
receipt therefore leaves the pooled paired input-reduction metric null rather
than comparing two cases against all three baselines.

| Case | Full-context arm | E0 budget-56 arm |
|---|---|---|
| Retry policy | 8,751 input tokens; `3,250`, pass | 562 input tokens; `3,250`, pass; 3 quotes visible |
| Session lifetime | 8,754 input tokens; `1800,300`, pass | 466 input tokens; `1800,300`, pass; 2 quotes visible |
| Retry function | 8,739 input tokens; `calculate_retry_delay`, pass | E0 abstained: `required_evidence_omitted`; no model call |
| **Total** | **3/3 pass; 26,244 input tokens** | **2/3 prepared and passed; no valid all-case savings ratio** |

For the first two fully paired cases only, E0 used 1,028 versus 17,505 local
input tokens, retaining both exact answers. This 94.127% two-case figure is a
partial diagnostic and is not an all-case score. At budget 64, Iteration 125
prepared all three cases, passed 3/3, and measured 94.7264% local-model input
reduction. The verified tradeoff is therefore that budget 56 saves more on
two prepared prompts but loses the third task. Lower budgets do not yet meet
the overall 95% requirement.

## Identity and hardware

- Model: `Qwen/Qwen3.5-0.8B`, revision
  `2fc06364715b967f1860aea9cf38778875588b17`, BF16, no adapter.
- Context budget: 56. Fixture SHA-256:
  `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`.
- Runner SHA-256:
  `e55b3518d942f886d7febf00bd44231b694f143c404369157e18832ae483102d`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter126.json`,
  5,301 bytes, SHA-256
  `c9a96cb0051a3adb4dc6e78537b66513be78b921bb2f809bbd4fc4b41926a806`.
- Runtime: Python 3.13.15, PyTorch `2.14.0+cu132`, CUDA 13.2,
  Transformers 5.17.0, NVIDIA RTX 5060 Ti.
- Minimum sampled free RAM 13.8171%; minimum VRAM 75.3173%; 27 samples,
  telemetry valid. The 10% runtime floor held; Fit-03's 25% RAM start
  requirement did not.
- Storage admission reserved 100,000,000 bytes, included the Docker WSL
  model volume and hourly automation directory, and remained under 50 GB.
  C: had over 139 GB free. No provider request or spend occurred.

The result preserves both sides of the tradeoff: lower context can save more
tokens, but an evidence-preserving system must abstain if required information
falls out. The next useful search is between 56 and 64, followed by broader
code-change episodes; a product claim still requires paired frontier-only
success, call and token receipts, complete lifecycle accounting, cost, and
sustained engineering evidence.
