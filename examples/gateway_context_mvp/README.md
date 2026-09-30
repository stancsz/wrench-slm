# Wrench gateway context demo

This local, provider-free demo runs the current deterministic E0 context path
against three authored synthetic repository questions. It shows exact input
token counts using the pinned MiniMax M3 chat template and checks that each
question's required source quotes remain visible.

Run it from the repository root with the pinned offline tokenizer environment:

```powershell
& 'C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe' examples/gateway_context_mvp/run_demo.py
```

The script creates a temporary synthetic repository below
`C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\tmp` and removes it at
exit. It prints a JSON receipt; the measured receipt for this iteration is
stored at `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\demo-receipt.json`.

## Scope

The current three-case receipt reports 86.4327% ratio-of-sums input-token
reduction (19,289 baseline tokens to 2,617 prepared tokens) with all 7 required
quotes visible. It calls no model or provider. The fixture contains synthetic
service source/configuration and 240 repetitive synthetic log lines. This is
an exploratory E0 context-preparation result, not a task-completion score,
frontier-token or dollar saving, LoRA result, production result, or evidence of
all-day engineering. See the linked Iteration 098 evaluation report for
denominators, per-case results, hashes, failures, and verification limits.

The fixture and prompts are synthetic and must not be used as a substitute for
consented repository-task evaluation. Keep the 95/5/95 and 95%-cheaper product
gates unchanged.

## Local model episodes

[`run_local_model_mvp.py`](run_local_model_mvp.py) adds a one-question,
provider-free integration path: Wrench E0 selects the required function source,
the pinned local Qwen3.5-0.8B base model answers, and an exact identifier check
grades the result. Its runtime sampler starts before model loading and passes
a generation stop criterion that halts the next token when RAM/VRAM sampling
falls below 10% or telemetry fails. The preflight reserve still matters:
synchronous model loading cannot be interrupted by the generation criterion.
The reproduced Iteration 117 episode passed and measured
90.6507% fewer target-tokenizer prompt-input tokens (6,439 to 602). The local
model used 490 input and 6 output tokens and returned the exact expected
function name in 4.44 seconds.

[`run_local_model_matrix.py`](run_local_model_matrix.py) loads the same local
base model once and runs the three authored lookup questions. Iteration 119
verified 3/3 answers and measured 88.9590% ratio-of-sums target-tokenizer
prompt-input reduction (19,337 to 2,135 tokens), with all seven required
quotes visible. This does not compare task success with an uncompressed-model
arm or measure frontier tokens avoided.

[`run_local_model_budget_sweep.py`](run_local_model_budget_sweep.py) tests
ascending E0 context budgets and stops at the first budget with all three exact
answers verified. Iteration 121's first tested passing value was 64: all seven
quotes remained visible and 3/3 answers passed, with 91.3482% target-tokenizer
prompt-input reduction (19,337 to 1,673 tokens). Budget 48 passed two model
answers but E0 rejected the retry-function context for omitting required
evidence. Thus 64 is the smallest passing value tested, not a global optimum.
This remains a three-case synthetic lookup diagnostic, not a frontier-savings
or code-writing claim. See the Iteration 121 report for the preserved setup
failure, exact identities, and resource samples.

[`run_paired_local_context_baseline.py`](run_paired_local_context_baseline.py)
compares the full fixture and E0-prepared prompts on the same local model and
the same three questions. Iteration 125 passed 3/3 in both arms and reduced
the local model's input tokens by 94.7264% (26,244 to 1,384); including its
unchanged output, reduction was 94.6363%. The target-tokenizer prompt result
was 91.4051%. This is still a small local-model comparison, not a
frontier-only or product-token-savings result. The context budget is
configurable for a lower-budget paired sweep. Iteration 126 at budget 56
preserved only two cases; E0 abstained on the retry-function task because it
would omit required evidence, so its all-case savings ratio is null. See the
paired reports for both the pass and the fail-closed result. Iteration 127's
audit found that all legacy lookup prompts included the expected answer text;
their exact-answer passes are contaminated and must not support a task-quality
claim. Future paired runs use answer-blind prompts.

[`run_deterministic_lookup_comparator.py`](run_deterministic_lookup_comparator.py)
answers those three fixed fixture questions with `tomllib` and Python AST
parsing. Iteration 122 passed 3/3 with 1,203 in-memory source bytes examined
and 0.00188 seconds of parser time, using no model tokens. Iteration 123 added
fixture-hash pinning and four fail-closed controls for duplicate TOML keys,
missing values, duplicate Python symbols, and changed fixtures; all seven
positive and negative checks passed. This is evidence that the fixed
mechanical slice should stay deterministic; the timing excludes startup and
is not an end-to-end cost comparison. It does not establish frontier-token
savings or general engineering capability.

[`run_snapshot_rule_route_lookup.py`](run_snapshot_rule_route_lookup.py) uses
Wrench's actual snapshot-bound E0 rule route, then parses only the retrieved
source. Iteration 124 passed the same 3/3 answers and three fail-closed
controls for an absent path, an unsupported code-change request, and source
mutation after snapshot. It records source hashes and read bytes. This is the
best current Wrench mechanical-path evidence, but it still does not establish
frontier-token savings or a broad task success rate.

Run it only from the repository root with the pinned local runtime and its
already installed adapter-side dependencies. Before a fresh run, take a new
resource sample, pass storage status and reserve admission, and use a new job
ID and receipt path. This example uses Iteration 120 names to avoid overwriting
the measured Iteration 119 receipt:

```powershell
$env:WRENCH_DEMO_JOB_ID = 'WRENCH-DEMO-LOCAL-MODEL-MATRIX-ITER120'
$env:WRENCH_DEMO_OUTPUT_PATH = 'C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\local-model-matrix-iter120.json'
$env:WRENCH_LORA_ADDONS = 'C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons'
$env:HF_HOME = 'C:\wrench-slm-data\cache\huggingface\gateway-demo'
$env:TORCH_HOME = 'C:\wrench-slm-data\cache\torch\gateway-demo'
& 'C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe' examples/gateway_context_mvp/run_local_model_matrix.py
```

Run the adaptive budget sweep with a new one-shot receipt path and job ID:

```powershell
$env:WRENCH_DEMO_JOB_ID = 'WRENCH-DEMO-BUDGET-SWEEP-ITER122'
$env:WRENCH_DEMO_OUTPUT_PATH = 'C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\budget-sweep-iter122.json'
$env:WRENCH_LORA_ADDONS = 'C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons'
$env:HF_HOME = 'C:\wrench-slm-data\cache\huggingface\gateway-demo'
$env:TORCH_HOME = 'C:\wrench-slm-data\cache\torch\gateway-demo'
& 'C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe' examples/gateway_context_mvp/run_local_model_budget_sweep.py
```

Run the answer-blind paired baseline and Wrench E0 arms. This guard rejects a
prompt if it contains its expected answer literal:

```powershell
$env:WRENCH_DEMO_JOB_ID = 'WRENCH-PAIRED-LOCAL-CONTEXT-ITER130'
$env:WRENCH_DEMO_OUTPUT_PATH = 'C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\paired-local-context-iter130.json'
$env:WRENCH_DEMO_CONTEXT_BUDGET = '63'
$env:WRENCH_LORA_ADDONS = 'C:\wrench-slm-data\envs\wrench-gateway-lora-screen-01-addons'
$env:HF_HOME = 'C:\wrench-slm-data\cache\huggingface\gateway-demo'
$env:TORCH_HOME = 'C:\wrench-slm-data\cache\torch\gateway-demo'
& 'C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe' examples/gateway_context_mvp/run_paired_local_context_baseline.py
```

Iteration 129 adds a format-aware, deterministic answer verifier and reruns
these same answer-blind tasks at budget 64. It passed 3/3 E0 cases versus
2/3 full-context cases, with 94.8236% local-model input-token reduction.
Iteration 130 lowers the budget to 63; E0 then abstains on a task whose required
evidence would be omitted, so the all-case ratio is undefined. These synthetic
results are not frontier-token savings or product acceptance. See the
[Iteration 129 report](../../docs/evals/wrench-gateway-model-research/iteration-129-answer-blind-format-aware-paired-baseline-20260928.md)
and [Iteration 130 report](../../docs/evals/wrench-gateway-model-research/iteration-130-answer-blind-budget63-abstention-20260928.md).

Run the deterministic mechanical comparator and its fail-closed controls
without model dependencies:

```powershell
$env:WRENCH_DEMO_JOB_ID = 'WRENCH-DETERMINISTIC-GUARD-ITER124'
$env:WRENCH_DEMO_OUTPUT_PATH = 'C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\deterministic-guard-iter124.json'
& 'C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe' examples/gateway_context_mvp/run_deterministic_lookup_comparator.py
```

Run the snapshot-bound Wrench route comparator with a new one-shot receipt:

```powershell
$env:WRENCH_DEMO_JOB_ID = 'WRENCH-SNAPSHOT-RULE-LOOKUP-ITER125'
$env:WRENCH_DEMO_OUTPUT_PATH = 'C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\snapshot-rule-lookup-iter125.json'
& 'C:\wrench-slm-data\envs\wrench-local-synthetic-cp313\Scripts\python.exe' examples/gateway_context_mvp/run_snapshot_rule_route_lookup.py
```

The output path is one-shot; use a new job ID and output filename for another
episode. The local-model cases remain authored synthetic lookups, use no
trained LoRA, call no frontier route, and do not measure frontier tokens
avoided, broad coding success, cost savings, or sustained operation. Missing
optimized Qwen kernels were reported at runtime. See the per-iteration reports
for denominators, resource samples, hashes, and failed setup attempts.
