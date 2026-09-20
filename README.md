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
request. Stock Ollama, vLLM, GGUF, native dense 4M retrieval quality, MiniMax
parity, and production throughput are not yet claimed.

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
current v44 package was re-run on the prompt-complete 220-case mechanical
contract: 220/220 expected outcomes, 120/120 exact eligible proposals,
zero prohibited accepts, zero model calls, and 0.594 ms median / 42.204 ms p95
through the embedded route. This is a package and mechanical-contract result,
not MiniMax parity, native dense 4M retrieval quality, or production utility.

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
