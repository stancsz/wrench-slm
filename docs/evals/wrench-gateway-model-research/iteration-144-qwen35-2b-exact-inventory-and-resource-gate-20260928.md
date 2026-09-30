# Iteration 144: exact Qwen3.5-2B inventory and local run gate

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-2B-INVENTORY-RESOURCE-GATE-ITER144`  
Status: **the pinned 2B snapshot is confirmed at 4,571,274,023 bytes across 13 files; storage is available, but defer model loading until a larger RAM margin is available**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question

Can the current leading small-controller candidate, Qwen3.5-2B, be advanced to
a same-task local comparison now, and is its exact package small enough to
admit under the Wrench storage boundary?

## Pinned upstream identity

The Hugging Face model API was queried read-only with `revision=` pinned to
`15852e8c16360a2fea060d615a32b45270f8a8fc`. It returned the same commit and
13 files totaling **4,571,274,023 bytes**. The sole weight shard is
4,548,221,488 bytes. The remaining 12 files are configuration, license,
tokenizer, vocabulary, chat-template, and image/video processor metadata.
The model card identifies the repository as Apache-2.0, a 2B causal language
model with a vision encoder. The local serving experiment will use text-only
inputs and the pinned Transformers snapshot.

| File | Bytes |
|---|---:|
| `.gitattributes` | 1,570 |
| `LICENSE` | 11,544 |
| `README.md` | 62,814 |
| `chat_template.jinja` | 7,755 |
| `config.json` | 2,908 |
| `merges.txt` | 3,353,259 |
| `model.safetensors-00001-of-00001.safetensors` | 4,548,221,488 |
| `model.safetensors.index.json` | 64,460 |
| `preprocessor_config.json` | 390 |
| `tokenizer.json` | 12,807,982 |
| `tokenizer_config.json` | 16,709 |
| `video_preprocessor_config.json` | 385 |
| `vocab.json` | 6,722,759 |
| **Total** | **4,571,274,023** |

The revision, exact file set, and bytes are pinned, but per-file cryptographic
digests have not yet been materialized in a local manifest. Verify every
downloaded file against upstream metadata before loading it. Do not treat the
revision and byte total as a substitute for that post-download hash check.

## Storage and hardware admission

Immediately before documenting this result, the storage checker included the
repository, approved Wrench root, Docker WSL model volume, and automation
directory. It reported 15,434,859,122 actual bytes, 7,103,000 bytes in existing
reservations (including this report's 1,000,000-byte reservation), no scan
errors, and **WITHIN_LIMIT**. The projected total was 15,441,962,122 bytes,
leaving 34,558,037,877 bytes below the strict 50 GB boundary. C: had
139,265,286,144 bytes free, far above the required 5 GB destination margin.
The inventory supports a conservative 2x snapshot staging estimate of
9,142,548,046 additional bytes; even with that peak, the current aggregate
would remain below the ceiling. This is a download/storage estimate, not a
measured model-load or training peak.

The live host sample was 6,609,668 / 33,486,624 KiB free system RAM (19.74%)
and 15,222 / 16,311 MiB free VRAM (93.32%) on an NVIDIA GeForce RTX 5060 Ti.
The general 10% reserve was met at the sample. However, the analogous 0.8B
paired run previously sampled a 13.476% RAM minimum. Since the 2B load path's
CPU staging peak has not been measured, starting it at the current 19.74%
free RAM risks crossing the 10% reserve. Defer the 2B model load until a fresh
sample has at least 25% free RAM, then monitor RAM and VRAM continuously with
an immediate stop on telemetry failure or a 10% boundary. The 25% threshold
here is a conservative launch margin for this unmeasured 2B load, not a claim
that the model has passed fit.

## Decision and next action

This inspection confirms that Qwen3.5-2B remains the first learned-controller
challenger to compare against 0.8B and deterministic-only. It does not make
2B a final winner. The research basis is the external task-specific LoRA
pruning evidence described in the model-size decision; Wrench has not run a
2B common-task comparison, trained a 2B Wrench adapter, or shown an end-to-end
frontier saving from either size.

When the RAM margin opens, the next bounded sequence is: reserve the exact
download peak; download only the pinned 13-file snapshot under
`C:\\wrench-slm-data`; verify each file and the total; run a single guarded
text-only load/generation preflight; then prepare the frozen same-task
deterministic-only / 0.8B / 2B comparison. Keep held-out data sealed. Training
still requires a fresh exact-hash package review, a >=25% RAM start sample,
the approved synthetic train/dev rows, and its own peak storage reservation.

## Evidence limits

This is upstream metadata and host-admission evidence only. No model was
downloaded, loaded, trained, or benchmarked. No provider request was sent, no
credentials were read, and SubRoute was not changed. The 95% local completion,
<=5% frontier routing, >=95% success retention, >=95% frontier-token and
all-in-cost reductions, and all-day engineering remain unproven.

## Sources

- [Pinned Qwen3.5-2B model card](https://huggingface.co/Qwen/Qwen3.5-2B/blob/15852e8c16360a2fea060d615a32b45270f8a8fc/README.md)
- [Pinned Qwen3.5-2B upstream inventory API](https://huggingface.co/api/models/Qwen/Qwen3.5-2B?blobs=true&revision=15852e8c16360a2fea060d615a32b45270f8a8fc)
- [Model-size evidence refresh](../../reports/wrench-gateway-model-research/model-size-decision-refresh-iter143-20260928.md)
- [Iteration 140 local paired result](iteration-140-exact-symbol-span-paired-20260928.md)
