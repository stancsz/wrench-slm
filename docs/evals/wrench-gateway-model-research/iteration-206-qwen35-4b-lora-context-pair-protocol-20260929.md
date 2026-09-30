# Iteration 206: Qwen3.5-4B Wrench LoRA context-pair protocol

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER206-20260929-01`  
Nonce: `8ea69481-5d65-4c7a-8a56-8d3b3a27148d`  
Repository HEAD required: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256 required: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question

Iteration 197 selected Qwen3.5-4B as the strongest current experiment lead,
not a product winner. Iteration 205 did not load a model because the selected
Python interpreter lacked its pinned runtime. Iteration 206 reuses the same
small synthetic development cases to test whether the pinned screen-03 Wrench
LoRA preserves exact answers when deterministic Wrench context replaces the
full fixture context. This is a local model/context diagnostic, not a fresh
holdout or coding-engineering benchmark.

## Pinned inputs

- Runner:
  `examples/gateway_context_mvp/run_qwen35_4b_lora_context_pair_iter206.py`,
  SHA-256 `E9B646AEA4C04B3739EA949DB82147E55A5B922CA4917BA28F1CF9CFEAE1C55C`.
- Runtime environment:
  `C:\wrench-slm-data\envs\wrench-gateway-py313-cu132-iter206`; 38 exact
  package versions in
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iter206-python-runtime-packages.txt`,
  SHA-256 `46576C195C4A131D063D952C10175C5D54C0F4079CDFF54815BF50C9594D4687`.
  Runtime environment report SHA-256
  `CF8F44CF3FC145EE776612A25D81E0006027825BFE17C5472DD90AA6A9D57F23`.
- Model: `Qwen/Qwen3.5-4B`, revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, 14-file inventory SHA-256
  `30b09cf32f06fae5418a0b925820202bfddf9e1c2a1f009d12e6396d10aed15a`,
  snapshot verification receipt SHA-256
  `8ff3a6587850b5bbd68a047f94d8d9dd28fd082a6d23a1f189c216ac2ebc8bd2`.
- Adapter: screen-03 fit-01, loaded inactive for evaluation only; weights
  SHA-256 `051a942cc306d15ff22ad300d6256cc4b8e6335b9c6263b65696353b04938e5c`,
  config SHA-256
  `f77ecf3c2e87b2586563f3ca6017b74f62b180c31f67260a590ccff85453531f`.
- Cases: the same three reused authored development cases from Iteration 205:
  `retry-policy`, `session-lifetime`, and `retry-function`. This data is not a
  holdout; do not open any sealed split.

## Execution and measures

Run exactly the new runner with the exact isolated interpreter path and
package-manifest hash. It compares every installed distribution and version
to the 38-package manifest, checks the installed Torch `direct_url.json`
against the exact wheel URL, and pins
Python 3.13.15, Torch `2.14.0+cu132`,
Transformers `5.17.0`, PEFT `0.21.0`, CUDA `13.2`, and GPU name/UUID
`NVIDIA GeForce RTX 5060 Ti` /
`GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021` before hashing the model or loading
weights. Use BF16, greedy decoding, at most 32 output tokens, one attempt per
case/arm, alternating context and model-arm order, and no retries.

Compare full fixture context with deterministic Wrench compact table/symbol
context, for both base and LoRA. Use strict decoded-string equality. Preserve
every answer, prompt hash, source snapshot identity, exact local Qwen tokenizer
input/output count, latency, load time, peak memory, and sampled RAM/VRAM floor.
Compute token ratios only if all three cases have one row for each context in
that model arm; otherwise report `null` and mark incomplete. Failed/aborted
runs retain an atomic no-clobber receipt.

The runner is provider-free: offline model flags and Python socket-connect
blocking. No Frontier/SubRoute request, tool call, credential read, repository
mutation by the model, or candidate activation is permitted. Zero provider
calls means Frontier savings and all-in cost savings remain `null`. Local
Qwen tokenizer ratios are not Frontier usage. Record failures and limitations;
an all-pass result cannot establish representative quality, confidence,
training generalization, route rate, cost, or all-day engineering reliability.

## Admission

- Output receipt:
  `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iteration-206-qwen35-4b-lora-context-pair.json`.
- The exact run and bounded receipt share reservation
  `WRENCH-QWEN35-4B-LORA-CONTEXT-PAIR-ITER206-20260929-01`, 100,000,000
  bytes. Do not reuse or overwrite Iteration 205 output.
- Immediately before run, recheck the storage budget including the hourly
  automation directory and Docker model volume. Keep at least 5 GiB physically
  free on C:. Require fresh RAM and VRAM with at least 10% free and keep those
  floors throughout. Confirm the unique output is absent, HEAD/goal identities
  match, and the pinned model/adapter hashes pass.
- The already-installed runtime occupies about 3.20 GB under the approved
  storage root. Keep the adapter inactive and all temporary/cache paths under
  that root.

This protocol admits only the bounded local diagnostic. It does not authorize
Frontier spend, production routing, activation, or held-out access.
