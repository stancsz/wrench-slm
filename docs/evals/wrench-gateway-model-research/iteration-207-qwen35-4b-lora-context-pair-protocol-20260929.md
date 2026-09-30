# Iteration 207: corrected Qwen3.5-4B LoRA context-pair protocol

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-QWEN35-4B-LORA-CONTEXT-ITER207-20260929-01`  
Nonce: `bb6a95d6-20fb-41af-9d4e-353522f36537`  
Repository HEAD required: `af01304824f079a64b6c3902397a2034b843511a`  
Active goal SHA-256 required: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Reason for correction

Iteration 206 completed the three synthetic paired lookups but strict scoring
gave 0/3 because every decoded answer had a trailing newline. PEFT also warned
that adapter keys were missing. The saved adapter contains 64 tensors under
`model.language_model.layers.*`; Iteration 206 loaded the base with
`AutoModelForCausalLM`, while the screen-03 trainer uses
`AutoModelForImageTextToText`. Those mismatched model wrappers made adapter
attachment unverified. Iteration 206 is preserved as inconclusive evidence.

Iteration 207 keeps the same bounded development cases and context comparison
to isolate these two execution defects. It uses the trainer's exact model
class, fails on PEFT missing/unexpected-key warnings, and compares every one
of the 64 saved adapter tensors byte-for-value with its attached LoRA
parameter before generation. It preserves raw decoded text and also applies a
predeclared output-boundary normalization that trims only surrounding ASCII
space, tab, carriage return, and line feed before exact expected-answer
comparison. This is ordinary response-boundary handling, not answer
canonicalization or post-hoc case selection.

## Pinned inputs

- Runner: `examples/gateway_context_mvp/run_qwen35_4b_lora_context_pair_iter207.py`,
  SHA-256 `8DEB4C80A1394C9B83616165101013C21D7A3E4E6A284A3676D37698D8E96144`.
- Runtime: Python 3.13.15, Torch `2.14.0+cu132`, Transformers `5.17.0`, PEFT
  `0.21.0`, CUDA `13.2`; isolated environment
  `C:\wrench-slm-data\envs\wrench-gateway-py313-cu132-iter206`; package
  manifest SHA-256
  `46576C195C4A131D063D952C10175C5D54C0F4079CDFF54815BF50C9594D4687`.
- Base: `Qwen/Qwen3.5-4B`, revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, exact 14-file inventory
  SHA-256 `30b09cf32f06fae5418a0b925820202bfddf9e1c2a1f009d12e6396d10aed15a`,
  snapshot-verification receipt SHA-256
  `8ff3a6587850b5bbd68a047f94d8d9dd28fd082a6d23a1f189c216ac2ebc8bd2`.
- Inactive adapter: screen-03 fit-01, weights SHA-256
  `051a942cc306d15ff22ad300d6256cc4b8e6335b9c6263b65696353b04938e5c`,
  config SHA-256
  `f77ecf3c2e87b2586563f3ca6017b74f62b180c31f67260a590ccff85453531f`.
- Cases: `retry-policy`, `session-lifetime`, `retry-function`, the same three
  previously exercised authored synthetic development fixtures. They are not
  held out and are not representative engineering episodes.

## Execution and measures

Load the base with `AutoModelForImageTextToText`, matching
`tools/train_gateway_lora_screen_03_4b_gpu.py`, then attach the pinned PEFT
adapter. Before generation, require no missing/unexpected adapter-key warning
and exact value equality for every saved tensor against the expected attached
module. Record the model class and number/hash of validated attached keys.
If any assertion fails, stop before generating and preserve a failure receipt.

For each case, compare full fixture context and deterministic Wrench table or
symbol context, with adapter disabled and enabled. Use BF16, greedy decoding,
at most 32 generated tokens, one attempt per row, alternating arm order, and
no retries. Record raw answer, boundary-normalized answer, exact verification,
prompt hashes, source snapshot identity, local tokenizer counts, latency,
model load time, peak CUDA memory, and resource minima. Compute context token
ratios only when every case has exactly one full-context and one Wrench-context
row in that model arm. Preserve all failures.

The run is local-only and blocks Python socket connections. It makes no
Frontier/SubRoute calls, reads no credentials, accesses no held-out split, and
cannot activate or mutate adapters. A local tokenizer result does not measure
Frontier usage or dollars. Even a successful 3/3 result does not establish
generalization, representative coding success, routing rate, the 95/5/95
target, or all-day engineering reliability.

## Admission and output

- Output: `C:\wrench-slm-data\artifacts\wrench-gateway-model-research\iteration-207-qwen35-4b-lora-context-pair.json`.
- Require a fresh source-package review that matches these exact hashes. A
  review does not admit execution.
- Immediately before any run, obtain a unique 100,000,000-byte storage
  reservation, include the approved external Wrench roots and automation
  directory, verify C: has at least 5 GiB free, confirm output absence and no
  duplicate process, and sample at least 10% free system RAM and VRAM. Maintain
  both resource floors throughout. Do not call a provider.
- Preserve the adapter as inactive. Do not overwrite this runner, protocol,
  or any prior iteration output. Only the exact pinned run may write the unique
  receipt using the runner's bounded no-clobber path.
