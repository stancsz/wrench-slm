# Wrench Qwen3.6 Expert-Tier Evaluation

## Public portable package

The current public experimental artifact is available on Hugging Face:

`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M`

Copy the complete model directory with one command:

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M
```

The package is a normal Hugging Face Safetensors directory with the tokenizer,
embedded deterministic toolbelt, verifier, runtime metadata, and experimental
FreeToken launcher included. It is portable as a model directory, but it is
still an experimental artifact. The package-local model server has a verified
Ollama-shaped `/api/chat` and `/api/generate` surface that accepts a 4M-declared
request. The product value is the model-local hybrid path: Wrench accepts the
monster payload, mechanically maps and reduces it, retrieves bounded evidence,
and gives the small model a compact working context. Dense native attention over
all 4M tokens is an optional research comparison, not a Wrench selling point or
release gate. Stock Ollama, vLLM, GGUF, MiniMax parity, and production
throughput remain separately labelled claims.

GGUF is not just a file rename. A valid Wrench GGUF release needs a llama.cpp
or Ollama architecture adapter that preserves the hybrid attention, tokenizer,
long-context policy, and embedded tool contract. Until that adapter is tested,
the Hugging Face Safetensors package is the canonical copy-paste format.

Wrench's experimental specialized execution SLM targets narrowly defined,
independently verifiable developer-tool work. The project evaluates an
8-expert compact tier and a 16-expert larger tier pruned from Qwen3.6-35B-A3B.
The 32-expert path remains an optional BF16 structural experiment.

The compact BF16 checkpoint reports 3,881,244,016 actual parameters and the
16-expert checkpoint reports 4,888,532,336. Their ideal INT4 weight-only
estimates are about 1.81 GiB and 2.28 GiB. Actual text-only W4A16 NVFP4
artifacts are 3.188 GiB for 8 experts and 3.718 GiB for 16 experts. Both
passed bounded CUDA load and generation smokes. These are experimental
artifacts, not quality or production claims.

It may propose a bounded action or abstain. A separate verifier and router own
execution, fallback, accounting, circuit breaking, and rollback. The project is
not a general coding agent and has no autonomous-write authority.

The old 28-case fixture is retained only as historical regression evidence. The
strongest local v74 mechanical-worker receipt reports 94.0113% weighted
mechanical frontier-token coverage, 100% net frontier-token savings, 97.1208%
weighted Wrench success, zero fallbacks, zero prohibited accepts, 184.312 ms
median latency, and 296.324 ms p95 latency. A fresh v74 package accepted an
exact 4,000,000-token raw request through `/api/chat` in 51.659 ms. These are
hybrid MapReduce and mechanical-worker results. They are not dense native
attention, final public release authorization, or a claim of universal MiniMax
parity.

The latest calibration lineage records hash-stable training bytes and fresh
packed receipts. The 16E tier is the current more-useful experimental
candidate; the 8E tier remains the smaller and faster option. Neither tier is
production enabled.

The original 35B teacher baseline and the live MiniMax replay remain separate
comparison evidence. The generic-tool schema adapter used by the old teacher
baseline is not part of Wrench runtime.

The current package evidence is recorded in
[Phase 131](phases/phase-131-ollama-api/README.md) and
[Phase 132](phases/phase-132-v44-prompt-complete/README.md). The full repository
regression is `pytest -q`: 140 passed, 14 warnings.

See [GOAL.md](GOAL.md) for the governing contract. The preserved pre-restart
implementation is outside this repository under
`C:\Users\stanc\github\portfolio\archives\wrench-slm-2026-09-17-pre-restart`.

The phased execution plan is in [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).
See [docs/WRENCH_MODEL_TIERS.md](docs/WRENCH_MODEL_TIERS.md) for current paths,
selection guidance, and measured guarded comparisons.
See [docs/MODEL_ARTIFACT_TRANSFER.md](docs/MODEL_ARTIFACT_TRANSFER.md) for the
private Git LFS checkpoint and 5060TI synchronization procedure.
Phase evidence is kept under `phases/`; large local datasets remain outside Git.
