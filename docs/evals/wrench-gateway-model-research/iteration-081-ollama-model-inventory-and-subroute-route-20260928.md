# Iteration 081: installed Ollama models and SubRoute local-route check

Date: 2026-09-28 (America/Edmonton)

Assignment: `WRENCH-OLLAMA-INVENTORY-ITER081-20260928`

## Existing local model inventory

Read-only inspection of the existing `canada-local-platform-ollama-1` service
found two Ollama tags in the `local-ai-models` Docker volume. The manifest
hashes pin the installed tag assemblies; Ollama's model-list ID is also shown
for reference.

| Tag | Parameters / quantization | Model layer | Model-layer digest | Manifest SHA-256 |
| --- | --- | ---: | --- | --- |
| `qwen3.5:4b` | 4.7B / Q4_K_M; 262,144 context; tools, vision | 3,389,971,840 bytes | `sha256:81fb60c7daa80fc1123380b98970b320ae233409f0f71a72ed7b9b0d62f40490` | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` |
| `qwen3.5:0.8b` | 873.44M / Q8_0; 262,144 context; tools, vision | 1,036,034,688 bytes | `sha256:afb707b6b8fac6e475acc42bc8380fc0b8d2e0e4190be5a969fbf62fcc897db5` | `f3817196d142eaf72ce79dfebe53dcb20bd21da87ce13e138a8f8e10a866b3a4` |

Each manifest is 709 bytes. The 4B manifest also references a 475-byte config,
11,355-byte license and 65-byte parameter layer. The 0.8B manifest references
a 476-byte config, 11,354-byte license and the same 65-byte parameter layer.
There is one model layer per tag and no additional shard. `du -sb` reported
4,426,052,564 bytes for the complete `/root/.ollama/models` tree: both manifest
files, seven unique blobs and directory entries. No weight blob was read or
independently rehashed; identity here is the installed Ollama manifest and
layer metadata, not upstream source provenance.

The model data is in Docker named volume `local-ai-models`, mounted at
`/root/.ollama`. The Wrench storage checker cannot currently include this
Linux-volume path, so the 4.426 GB model store is not part of the Wrench
`WITHIN_LIMIT` total. Do not use these weights in a Wrench run until the volume
is included in storage accounting or an admitted copy is placed under
`C:\wrench-slm-data`. These quantized Ollama packages also do not replace the
pinned Hugging Face training snapshot for Fit-03.

## SubRoute route gap

The running gateway's `OLLAMA_API_BASE` is `http://host.docker.internal:11434`.
A read-only GET to `/api/tags` from inside `unified-llm-gateway` failed with
`URLError`; a host GET to `127.0.0.1:11434` was refused. Docker reports the
Ollama service on `canada-local-platform_default` and SubRoute on
`subroute_default`, with no published Ollama host port. The current SubRoute
`desktop` alias maps to `ollama/qwen2.5-coder`, which is not among the two
installed Ollama tags. The live `/models` list has 19 aliases, but this does
not make the local Qwen tags reachable through port 4000.

No running service configuration was changed. No model was loaded, and no
completion, provider, or inference request was made. This identifies a
promising under-10B coding-worker candidate, not that it runs smoothly or
works all day. Latency, tool-use quality, LoRA compatibility, task success and
token savings remain unmeasured.

## Resource and storage gate

At admission, RAM was 3,733.0 / 32,701.8 MiB free (11.42%); VRAM was 15,203 /
16,311 MiB free. Fit-03 remains about 4,442.5 MiB below its 25% free-RAM start
gate. The storage checker, with SubRoute and the Wrench hourly automation
included, reported `WITHIN_LIMIT` at 10,994,525,862 actual bytes and 6,103,000
bytes in existing reservations before this report's 75,000-byte reservation.
The external Docker model volume is stated separately above and was not
included in that total.

Next: retain Qwen3.5-0.8B as the admitted LoRA-fit candidate; if evaluating
Qwen3.5-4B as a coding worker, first solve storage accounting and the isolated
SubRoute-to-Ollama route, then run bounded latency and representative coding
checks only after RAM/VRAM admission. Do not restart or alter the active
port-4000 service as part of this report.
