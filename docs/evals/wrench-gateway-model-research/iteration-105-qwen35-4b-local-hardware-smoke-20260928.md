# Iteration 105: Qwen3.5-4B local hardware smoke

Date: 2026-09-28  
Assignment: `WRENCH-GW-LOCAL-MODEL-HARDWARE-SMOKE-106-20260928`  
Status: **not smooth on the currently installed Docker Ollama path; CPU-only load consumed host RAM and produced no answer before the run was stopped**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway goal SHA-256: `43278D00ED8D1061DAA11A5BFD522ADAAC5FEF7D800215677D59D6D0A43C84A6`

## Candidate identity

The read-only Ollama inventory showed `qwen3.5:4b`, reported as 4.7B
parameters / Q4_K_M. The installed Ollama model ID was `2a654d98e6fb`, full
manifest SHA-256 `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd`,
and model layer digest
`sha256:81fb60c7daa80fc1123380b98970b320ae233409f0f71a72ed7b9b0d62f40490`.
The installed Modelfile reports Apache-2.0. This pins the installed Ollama
assembly, not a complete training checkpoint or upstream training provenance.

## Attempt and result

Before the attempt, Windows reported 27.19% free RAM and 15,187 / 16,311 MiB
free VRAM. `ollama ps` showed no model loaded. A local one-line request was
sent directly to the existing Ollama container, not through SubRoute or an
external provider:

```text
docker exec canada-local-platform-ollama-1 ollama run --verbose --keepalive 5m qwen3.5:4b "Return exactly WRENCH_LOCAL_OK and nothing else."
```

The run did not return a completion. `ollama ps` reported the candidate as
`100% CPU` with context 4096. The container's exact `llama-server` process
showed the pinned model-layer hash, `-c 4096`, and no GPU allocation; NVIDIA
utilization remained 0%. Docker CPU use was about 100%. Sampled free system
RAM fell from 27.19% to 24.51%, 20.36%, 15.23%, and then 11.24%, while VRAM
remained about 15.2 GiB free. The server had accumulated about 3m51s CPU time
without returning output. The configured 10% RAM floor was not crossed in the
samples, but the declining reserve made continuing inappropriate.

The attached CLI interruption did not stop its container-side child. I
inspected the container process table, identified only this request's
`ollama run` PID 24044 and model-specific `llama-server` PID 24061, then sent
SIGINT to those exact PIDs. The persistent Ollama service PID 7 and Docker
services were left running. The model runner disappeared from the process
table; `ollama ps` retained a stale keepalive entry even after the runner
exited. RAM began recovering to 19.85%; VRAM was 15,221 MiB free. No model
output or usable latency measurement exists, so tokens/second is N/A.

I then started an isolated container named `wrench-ollama-gpu-smoke-107` with
`--gpus all --network none` and the existing `local-ai-models` volume mounted
read-only. Docker recorded a GPU device request, but the container had no
`/dev/nvidia0`; Ollama only logged that it was discovering GPUs. No inference
was sent through this container. At this sample, free RAM was 20.65% and
15,233 MiB of VRAM remained free. I stopped only the temporary container;
the original Ollama service stayed running. Free RAM recovered to 20.95% and
VRAM was 15,217 MiB free.

**Decision:** this installed Docker path does not pass the owner's smooth-run
gate. The failure does not establish that the same weights cannot run through
a CUDA-enabled host runtime; that path needs its own exact runtime admission.
The 0.8B candidate and other sub-10B candidates remain open. This is a
hardware-path rejection, not a model-quality comparison.

## Admission and scope

Storage admission explicitly included the Docker Desktop WSL model volume and
the active hourly automation directory. The job reserved 250,000,000 bytes;
the model files were already present and counted by the storage scan. C: had
over 143 GB free. No download, file copy, route modification, credential read,
SubRoute call, provider call, code task, LoRA fit, or adapter activation
occurred. The held-out data remained sealed.

This attempt only answers whether the installed Docker Ollama route can run
this candidate smoothly. It does not test Qwen task competence, Wrench prompt
reduction, LoRA behavior, local completion rate, frontier-token savings, or
the 95/5/95 and 95%-cheaper product criteria. The currently measured 86.4327%
E0 reduction remains a synthetic prompt-input component result.

## Next action

Evaluate the existing 0.8B Hugging Face snapshot and its established local
CUDA environment for a bounded LoRA/task MVP. If the 4B base remains a
candidate, use a host runtime with verified CUDA support or obtain explicit
service authority to repair Docker GPU exposure. Do not alter or restart the
owner's existing Docker/Ollama/SubRoute services. Any new run needs fresh
storage admission and resource sampling; keep the 10% RAM/VRAM reserve
throughout. The Fit-03 package review must also be refreshed against the
active goal hash before training.
