# Iteration 205: Qwen3.5-4B Wrench LoRA context-pair protocol

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER205-20260929-01`  
Nonce: `bd261641-cb41-48c1-bd3f-fdb6cc44e46f`  
Repository HEAD required: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256 required: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Decision this screen informs

Iteration 197 found Qwen3.5-4B to be the most promising current experiment
candidate, not a product winner. This paired local screen asks whether its
already trained Wrench LoRA preserves the 4B base's exact answers when Wrench
replaces full synthetic repository context with selected table or symbol
evidence. It advances the selected-model and local-context hypotheses. It does
not establish the 95/5 workload, Frontier token savings, cost savings, or
all-day software engineering.

## Frozen inputs and arms

- Three previously exercised, authored development cases from
  `examples/gateway_context_mvp/run_demo.py`: `retry-policy`,
  `session-lifetime`, and `retry-function`. This is reused development data,
  not a fresh holdout. Do not inspect or use any sealed payload.
- Same exact prompt, task fixture, and deterministic exact-string verifier in
  each paired arm. Compare `full_context` with `wrench_table_context` for both
  `base` and the inactive screen-03 `wrench_lora` adapter.
- The adapter is loaded only for evaluation. Do not activate, promote, or
  write it. No tool, shell, repository-edit, provider, or SubRoute calls are
  allowed. No credentials are read. Python socket connections are blocked by
  the runner; this is not OS-level isolation.
- Model: `Qwen/Qwen3.5-4B`, revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, Apache-2.0; exact 14-file,
  9,342,907,469-byte manifest and local snapshot are rehashed at launch.
- Adapter: screen-03 fit-01, exact adapter weights SHA-256
  `051A942CC306D15FF22AD300D6256CC4B8E6335B9C6263B65696353B04938E5C`;
  config SHA-256
  `F77ECF3C2E87B2586563F3CA6017B74F62B180C31F67260A590CCFF85453531F`.
- Runtime gates Python major/minor `3.13` (recording full `sys.version`), Torch
  `2.14.0+cu132`, Transformers `5.17.0`, PEFT `0.21.0`, CUDA `13.2`, and
  `nvidia-smi` name plus UUID `NVIDIA GeForce RTX 5060 Ti` /
  `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. BF16, greedy decoding, maximum
  32 generated tokens, one pass per pair, no retries. Model-arm order also
  alternates by case to reduce first-arm warm-up bias.

## Measures and interpretation

Report every answer and strict decoded-string pass/fail, with no trimming of
whitespace or backticks. For each model arm, report sums of
exact local Qwen tokenizer input tokens and input-plus-output tokens in the
full and Wrench contexts. The ratios are local-tokenizer context proxies only.
Record latency, model load time, peak CUDA memory, RAM/VRAM minima, model and
adapter hashes, prompt hashes, source snapshot identities, and every failed or
aborted case. Zero Frontier calls means Frontier savings and all-in cost are
`null`, not 100%.

The fixture has only three repeated synthetic lookup cases. An all-pass result
can prioritize further evaluation but cannot support representative utility,
confidence, training generalization, or product claims. Any failure rejects
that context/model arm for this screen and remains in the receipt.

## Admission and output

- Exact runner receipt:
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iteration-205-qwen35-4b-lora-context-pair.json`.
- Keep all work within the existing 100,000,000-byte reservation for this job;
  do not download, extract, fit, package, or open held-out data.
- Immediately before the run, require a fresh storage status including the
  hourly automation directory and Docker Ollama model volume; `C:` must retain
  at least 5 GB physically free after the reservation. Require fresh RAM and
  VRAM samples with at least 10% free, and keep both floors throughout.
- The runner refuses a preexisting output, mismatched HEAD/goal/model/adapter or
  GPU identity, Python/runtime mismatch, resource breach, or output over 256 KiB.
  It writes success, incomplete-run, or early-failure receipts with exclusive
  atomic no-clobber creation. Ratios are `null` unless each of the three cases
  has exactly one row for each context in that model arm. The operator records
  the immediate pre-run storage-check output, active reservation ID, C: free
  bytes, and final receipt byte count/SHA-256 alongside the result. Storage
  admission is an external gate and is not inferred from runner success.
- Release the storage reservation only after the process stops and its output
  size and SHA-256 are recorded. Leave the candidate inactive.

## Run authority boundary

This protocol and its static review admit only the bounded, provider-free local
screen if fresh resource and storage checks pass. They do not authorize a
provider request, spend, production routing, adapter activation, or access to
the held-out split.
