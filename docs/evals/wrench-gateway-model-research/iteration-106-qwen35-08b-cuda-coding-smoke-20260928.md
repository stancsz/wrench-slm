# Iteration 106: Qwen3.5-0.8B CUDA code-generation smoke

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-GW-08B-CUDA-TASKSMOKE-108-20260928`  
Status: **model loaded and generated on CUDA, but the bounded code task failed deterministic verification because the answer was truncated mid-expression**  
Model snapshot: `Qwen/Qwen3.5-0.8B`, revision `2fc06364715b967f1860aea9cf38778875588b17`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`

## Task and exact runtime

The frozen prompt asked the model to return one Python function implementing
bounded exponential retry delay, with type, sign, finite-number, and cap
validation. A syntax-aware deterministic harness admitted only one function,
an optional plain `import math`, a small AST allowlist, and a restricted set of
builtins before running six valid/invalid cases. The model output did not pass
parsing, so no generated code was executed and no task case passed.

The run used the existing pinned Hugging Face snapshot at
`C:\\wrench-slm-data\\weights\\Qwen3.5-0.8B`, Transformers `5.17.0`, PyTorch
`2.14.0+cu132` (CUDA build `13.2`), the NVIDIA RTX 5060 Ti, and BF16 inference.
`trust_remote_code=False` and `local_files_only=True`. CUDA initialized and
reported one device. This run did not train or load an adapter. PEFT files
were present at
`C:\\wrench-slm-data\\envs\\wrench-gateway-lora-screen-01-addons\\peft`,
but that add-ons directory was not on this run's Python import path. The
earlier environment check therefore did not establish that PEFT was absent
from the machine. Transformers warned that
`causal_conv1d` and `flash-linear-attention` were missing and used reference
PyTorch implementations.

| Measure | Result |
|---|---:|
| Input | 109 model-tokenizer tokens |
| Generated | 220 tokens, exactly the configured limit |
| Model load | 9.853 s |
| Generation | 65.233 s, about 3.37 output tokens/s |
| Peak CUDA allocated / reserved | 1,725.6 / 1,808.0 MiB |
| Lowest sampled free system RAM | 15.09% (4,934 MiB) |
| Lowest sampled free GPU memory | 13,181 / 16,311 MiB |
| Deterministic syntax and behavior verification | **Failed** |

The response spent many tokens on a docstring and typing annotations, then
ended inside a tuple expression at `if not isinstance(base, (int`. AST parsing
raised `SyntaxError: '(' was never closed`. The configured output cap and
observed verbosity contributed to the failure. This single base-model sample
does not estimate a success rate, test Wrench context selection, measure token
savings, or evaluate a trained LoRA; it is a concrete quality/latency failure
for this prompt and runtime. The earlier smoke-script failure was a harness
ordering bug before model loading and is not counted as a model result.

## Decision impact

This confirms local CUDA feasibility for the exact 0.8B BF16 snapshot under
the present software stack, with reserves maintained, but does not establish
that it runs smoothly for a representative coding workload. Missing optimized
kernels materially affected the measured latency. Combined with the previous
0.8B general semantic screen and the external LoRA pruning evidence for 2B,
it strengthens the provisional choice of **2B for the bounded Wrench
controller**. It does not prove 2B local fit or utility. For a single local
coding worker, no 0.5B-12B candidate has passed representative task and
eight-hour engineering gates.

Next, pin/confirm a compatible optimized runtime and run the same frozen task
suite on the 0.8B base, a deterministic-only Wrench arm, and an admitted 2B
LoRA candidate. Compare exact prepared evidence, verifier outcomes, full
latency, local compute and tokens. Do not open the held-out split or infer
95/5, 95% frontier savings, 95% lower cost, or all-day reliability from this
single smoke. Keep SubRoute `:4000` unchanged and provider calls closed.

## Admission and cleanup

The storage checker admitted this bounded job under
`WRENCH-GW-08B-CUDA-TASKSMOKE-108-20260928` with a 300,000,000-byte peak
reservation; checks included `C:\\wrench-slm-data`, the Docker Desktop WSL
model volume, the hourly automation directory, sibling/worker checkouts, and
the previously inventoried temporary Wrench tree. C: had 133.91 GiB free at
launch. The prompt and response were retained in the execution receipt
recorded here; no model file, dataset, adapter, checkpoint, route setting, or
temporary repository was written. The model process exited normally, and free
RAM returned to 21.48% with 15,216 MiB GPU memory free. Release the storage
reservation only after this report is counted and a final storage status is
clear.
