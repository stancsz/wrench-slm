# Qwen2.5-Coder-7B fit feasibility screen

Date: 2026-09-27 (America/Edmonton)
Status: metadata-complete challenger; not selected, downloaded, or fit

## Decision question

Does a code-specialized model below 10B offer a plausible local worker and
Wrench-LoRA candidate on the RTX 5060 Ti, without assuming that parameter count
or a published memory profile proves this host can train it smoothly?

## Candidate identity and full repository inventory

The live Hugging Face model API returned revision
`c03e6d358207e414f1eca0bb1891e29f1db0e242`, license `apache-2.0`, 14 files,
and 15,242,807,397 total bytes. The four safetensors shard SHA-256 values came
from that API. Other file byte sizes are pinned through the full commit.

| File | Bytes | SHA-256 when provided |
| --- | ---: | --- |
| `.gitattributes` | 1,519 | commit-pinned |
| `LICENSE` | 11,343 | commit-pinned |
| `README.md` | 6,392 | commit-pinned |
| `config.json` | 663 | commit-pinned |
| `generation_config.json` | 242 | commit-pinned |
| `merges.txt` | 1,671,839 | commit-pinned |
| `model-00001-of-00004.safetensors` | 4,877,660,776 | `0b6f069918b07c064cbba8ae4f00f529aa9bbf84b7cdfcb7fc2694a40f6aa8ef` |
| `model-00002-of-00004.safetensors` | 4,932,751,008 | `c3d46733e7aa054ea7b063fbccd0a5a08446e7bd1814bef26936c5aa1331da62` |
| `model-00003-of-00004.safetensors` | 4,330,865,200 | `9fe45dacee087385b3d2d6dd27a7413a8a56d95f145772facc148fa86fc73446` |
| `model-00004-of-00004.safetensors` | 1,089,994,880 | `5aa6e5cbe642377fd441fb4e60e83cca96b2bcd9820e245b9ea06d94653f17f2` |
| `model.safetensors.index.json` | 27,752 | commit-pinned |
| `tokenizer.json` | 7,031,645 | commit-pinned |
| `tokenizer_config.json` | 7,305 | commit-pinned |
| `vocab.json` | 2,776,833 | commit-pinned |
| **Total** | **15,242,807,397** | |

The pinned `config.json` identifies `Qwen2ForCausalLM`, 28 layers, 28 query
heads, 4 key/value heads, BF16 source weights, and a 32,768-token configured
context. The model card describes 7.61B parameters and a 131,072-token context
extension using YaRN. The candidate is code-specialized, which makes it a
plausible local code-worker challenger. Tool-call behavior and Wrench-task
quality are unverified.

## Hardware and training evidence

The current machine is an RTX 5060 Ti with 16,311 MiB VRAM. The live sample had
15,224 MiB free. System RAM was 3,297.1/32,701.8 MiB free (10.08%), far below
the 25% training start gate and with little margin over the 10% runtime floor.
No model file was downloaded and no model was loaded.

Qwen's official fine-tuning guide documents QLoRA profiles for its Qwen-7B-Chat
on one A100 80GB, batch size 1 and gradient accumulation 8. The table reports
13.9 GB at sequence length 2,048 and 12.3 GB at 1,024. Hugging Face PEFT's
current guide describes 4-bit bitsandbytes NF4 loading with LoRA and
`prepare_model_for_kbit_training`. These are evidence that the method is
established and a 7B profile may fit within 16GB VRAM at short context. They
are not measurements for Qwen2.5-Coder, an RTX 5060 Ti, the pinned Wrench
runtime, or this host's system RAM. A bounded local preflight is still required.

The existing Wrench environment pins Python 3.13.15, Torch 2.14.0+cu132,
Transformers 5.17.0, PEFT 0.21.0, and Accelerate 1.15.0 for Qwen3.5-0.8B.
No `bitsandbytes` package directory is present in the runtime or LoRA add-on
directories. The current screen-02 trainer explicitly requires Qwen3.5 model
type, loads `AutoModelForImageTextToText`, and uses FP32. It cannot be reused
unchanged for this Qwen2 causal model or a QLoRA run. Installing or pinning a
candidate-specific dependency environment requires its own complete package
inventory, storage reservation, exact-hash review, and hardware preflight.

## Storage accounting

Before a download, storage was `WITHIN_LIMIT` at 10,992,554,978 actual bytes
plus 8,103,000 bytes of existing reservations. One full candidate snapshot
would project to 26,235,362,375 actual bytes, or 26,243,465,375 including the
existing reservations. Conservatively allowing a second full snapshot copy
for cache/materialization would project to 41,478,169,772 actual bytes, or
41,486,272,772 including current reservations. That leaves 8,513,727,228 bytes
under the strict 50 GB ceiling for a bounded adapter, runtime additions, and
receipts. The C: volume had about 132.17 GiB free.

The proposed QLoRA path quantizes the source while loading it and need not
write a separate quantized base copy. Any explicit converted checkpoint,
duplicate cache, package environment, or additional retained version must be
added to the admission sum before starting the job. No download is approved or
started by this metadata screen.

## Disposition

Add this as a serious **code-worker and Wrench-LoRA challenger**, not a winner.
Its code specialization is better aligned with sustained engineering than a
sub-1B general controller, while its 7.61B size and QLoRA route could plausibly
fit this GPU at a bounded context. This is a literature-supported hypothesis,
not evidence that it runs smoothly here. Keep the Qwen3.5-0.8B path as a separate
already-staged controller experiment. Do not pool their results.

The next candidate-specific step is an offline reviewed QLoRA protocol and
runner for this exact pinned model. When the machine reaches the start gate,
run a one-step preflight at batch size 1 and sequence length 512, monitor RAM
and VRAM continuously, then raise context only after the measured reserve
allows it. Do not proceed to full training until that receipt proves the
runtime identity, exact targets, finite step, and resource envelope. Held-out
scoring and paired code-task utility remain separate gates.

## Sources

- [Pinned Qwen2.5-Coder-7B-Instruct model card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct?revision=c03e6d358207e414f1eca0bb1891e29f1db0e242)
- [Complete pinned model tree](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/tree/c03e6d358207e414f1eca0bb1891e29f1db0e242)
- [Qwen's official LoRA and QLoRA training guide](https://github.com/QwenLM/Qwen/blob/main/recipes/finetune/deepspeed/readme.md)
- [Hugging Face PEFT quantization guide](https://huggingface.co/docs/peft/developer_guides/quantization)
