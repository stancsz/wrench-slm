# Iteration 037: Qwen3.5-2B inventory and SubRoute liveness (2026-09-27)

## Question

Does the current pinned Qwen3.5-2B inventory support admission for a local
Wrench LoRA candidate, and is the owner-designated SubRoute endpoint on port
4000 reachable without sending generation traffic?

## Findings

The Hugging Face model API was queried at the pinned revision
`15852e8c16360a2fea060d615a32b45270f8a8fc`. It returned the same revision,
2,274,069,824 parameters, and 13 files totaling **4,571,274,023 bytes**. This
supersedes the 4,561,029,470-byte total recorded in the earlier inventory
paragraph in [the research report](../../reports/wrench-gateway-model-research/research-20260927.md).
The difference is 10,244,553 bytes. The model has not been downloaded; this is
metadata inventory only.

| File | Bytes |
| --- | ---: |
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

The official card describes Qwen3.5-2B as a task-specific fine-tuning and
research model, with a 262,144-token native context. That advertised context
is not a safe Wrench runtime setting: start with a separately reviewed,
short-context profile and account for activations, KV cache, training state,
format/cache duplicates, and the 10% RAM/VRAM reserve. The present host is an
RTX 5060 Ti with 16,311 MiB VRAM. A sampled 15,100 MiB was free, but system RAM
was only 3,216.9/32,701.8 MiB free (9.84%). No fit, inference, or test was
admitted on that sample.

The closest public task match remains Squeez: its author reports LoRA on
Qwen3.5-2B for task-conditioned, verbatim tool-output extraction, with 0.86
recall, 0.80 F1, and 92% input-token removal on a curated 618-example test
set. This is encouraging evidence for a narrow context-pruning role. It also
falls short of the requested 95% token reduction and does not measure Wrench
task completion, engineering, cost, or all-day reliability. It supports a
candidate hypothesis, not model selection or a Wrench effectiveness claim.

The user-designated `http://127.0.0.1:4000` endpoint returned HTTP 200 for
read-only `GET /api/active-model` and `GET /v1/models`. The active-model
projection reported `active_model=openrouter`, `mode=force`, and
`policy_version=4`; the models endpoint listed 19 aliases. These GETs confirm
local gateway liveness only. They do not identify a generation's actual
upstream provider, verify billed cost, or authorize a provider call. No POST,
generation, or spend occurred. The numeric aggregate spend cap remains
unprovided, so the paid comparison remains closed.

## Decision and next gates

Keep the already staged Qwen3.5-0.8B narrow LoRA as the first low-cost
feasibility candidate only when its 25% RAM start gate and exact run admissions
pass. Do not download Qwen3.5-2B until held-out Wrench evidence identifies a
capacity-specific 0.8B failure. If that happens, the 2B candidate needs its
own pinned-source hash record, complete peak-storage reservation including
cache/staging/working copies and checkpoints, architecture-specific LoRA
target review, short-context runtime preflight, and held-out evaluation plan.
For either model, deterministic retrieval, parsing, provenance, validation,
tool authority, and exact recovery remain code-owned. Neither candidate is
currently demonstrated to perform sustained open-ended engineering alone.

Before any SubRoute generation, retain the :4000 route and force-mode
configuration, obtain a numeric campaign cap, and verify the caller reserves
worst-case cost before each request, fails closed on unknown/mismatched model
or provider, and records token and billed-cost receipts.

## Sources and observations

- [Pinned Qwen3.5-2B model API and file inventory](https://huggingface.co/api/models/Qwen/Qwen3.5-2B?blobs=true&revision=15852e8c16360a2fea060d615a32b45270f8a8fc)
- [Qwen3.5-2B official model card](https://huggingface.co/Qwen/Qwen3.5-2B)
- [Squeez paper, arXiv:2604.04979](https://arxiv.org/abs/2604.04979)
- SubRoute read-only GET observations: 2026-09-27, `127.0.0.1:4000`; no
  generation request made.
- Storage job admission: `WRENCH-QWEN35-2B-RECON-20260927-01`, 120,000-byte
  documentation reservation. No model artifact was produced.
