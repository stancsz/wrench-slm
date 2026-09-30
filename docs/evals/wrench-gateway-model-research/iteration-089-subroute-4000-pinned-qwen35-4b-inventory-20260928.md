# Iteration 089: SubRoute 4000 and pinned Qwen3.5-4B inventory

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-EVAL-ITER089-SUBROUTE-4000-QWEN35-4B-INVENTORY-20260928`

Status: **read-only gateway verified; candidate inventory pinned; inference is
not admitted**

Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a`

Gateway research goal SHA-256 at inspection:
`225D7250BA53C1F2FC63E999A619B53CC3D4E779BE3D3B4D5726829FA89D6D2F`

## SubRoute check

At `http://127.0.0.1:4000`, GET requests to `/health/liveliness`, `/models`,
`/v1/models`, and `/api/active-model` returned HTTP 200. The two model catalogs
listed 19 aliases. Active state was `openrouter`, mode `force`, policy version
4. This confirms the control plane is reachable; it does not establish a
working local inference route.

The SubRoute source maps `desktop` to `ollama/qwen2.5-coder`, with its Ollama
base URL supplied by `OLLAMA_API_BASE` (default `http://host.docker.internal:11434`).
The router's `force` mode routes requests to the active alias regardless of the
requested alias. Therefore a completion submitted now, even with
`model="desktop"`, would be routed to the active OpenRouter alias. No completion
was sent. The aggregate campaign spend cap remains unspecified, and this check
did not read credentials, modify configuration, or restart SubRoute.

## Pinned candidate inventory

The official Hugging Face metadata endpoint for
[`Qwen/Qwen3.5-4B`](https://huggingface.co/Qwen/Qwen3.5-4B), queried on
2026-09-28, resolved `main` to revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. The complete snapshot has 14 files
and sums to **9,342,907,469 bytes** (9.342907469 GB decimal):

| File | Bytes |
|---|---:|
| `.gitattributes` | 1,570 |
| `LICENSE` | 11,544 |
| `README.md` | 77,661 |
| `chat_template.jinja` | 7,756 |
| `config.json` | 3,161 |
| `merges.txt` | 3,353,259 |
| `model.safetensors-00001-of-00002.safetensors` | 5,329,398,688 |
| `model.safetensors-00002-of-00002.safetensors` | 3,990,429,408 |
| `model.safetensors.index.json` | 76,196 |
| `preprocessor_config.json` | 390 |
| `tokenizer.json` | 12,807,982 |
| `tokenizer_config.json` | 16,710 |
| `video_preprocessor_config.json` | 385 |
| `vocab.json` | 6,722,759 |
| **Total** | **9,342,907,469** |

This is an exact remote file inventory, not a local download or a training
admission. The existing Ollama `qwen3.5:4b` Q4_K_M package in Docker is a
different artifact identity, with a 3,389,971,840-byte model layer. It is not
the BF16 Hugging Face snapshot above. The Ollama package remains unreachable
through the current `desktop` route.

The storage checker currently inventories 15,418,742,541 bytes and 6,103,000
bytes of active reservations, including the Docker Ollama volume. Adding one
copy of the BF16 snapshot would bring the aggregate to at least
24,767,753,010 bytes. A cache plus staging or working copy would add a second
9,342,907,469 bytes before any LoRA output, checkpoint, optimizer state, or
logs. Any download or training run therefore still needs a complete peak-space
estimate, a fresh reservation, destination free-space check, and live resource
admission.

## Host gate and conclusion

At 2026-09-28 07:50 UTC, Windows reported 3,277.6 / 32,701.8 MiB free RAM
(10.02%). The RTX 5060 Ti reported 15,188 / 16,311 MiB free VRAM. The RAM
sample is only about 7.4 MiB above the 10% runtime floor and below the separate
25% Fit-03 start gate. No model load, inference, training, benchmark, provider
request, or held-out access was run.

Qwen3.5-4B remains a plausible larger LoRA challenger by file size and published
capability, but this iteration proves neither smooth local serving nor
engineering task quality. The immediate blocker for using the running gateway
is the forced OpenRouter route plus the disconnected Ollama endpoint. The 95/5
routing target, 95% outcome parity, 95% frontier-token or cost reduction, and
all-day engineering performance remain unproven.

## Sources and method

- Hugging Face metadata: [`Qwen/Qwen3.5-4B` revision API](https://huggingface.co/api/models/Qwen/Qwen3.5-4B/revision/main?blobs=true), read-only; returned the full commit SHA and per-file sizes above.
- Gateway: read-only GETs to the four local endpoints above.
- Route configuration: read-only inspection of SubRoute `config/litellm.yaml` and `src/unified_llm_gateway/plugins/dynamic_router.py`.
- Host: Windows memory query and `nvidia-smi`; storage: `python tools/check_wrench_storage_budget.py status` with the Docker volume and hourly automation as included roots.

The source metadata describes the current `main` resolution at inspection time.
Future admission must use the full pinned revision above, not a floating
`main` reference.
