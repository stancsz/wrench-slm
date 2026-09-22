---
library_name: transformers
license: apache-2.0
pipeline_tag: text-generation
tags:
- wrench
- code
- developer-tools
- qwen3.6
- long-context
- experimental-preview
---

# Wrench-4B-Qwen3.6-8E

> [!WARNING]
> **Experimental Preview. Not for production use.** This is a research and
> preview artifact. Do not deploy it in production or safety-critical
> workflows, and do not treat benchmark results as production validation.

Wrench is a bounded developer-tool execution SLM for fast, repetitive,
verifiable mechanical work. It proposes structured actions or abstains. An
independent verifier and the stronger-model fallback retain final authority.
Wrench never executes arbitrary shell commands, uses credentials, or writes
autonomously.

This experimental candidate is derived from Qwen3.6-35B-A3B, uses NVFP4 W4A16
weights, and contains `3,881,244,016` verified parameters, below the 4.25B
parameter ceiling. It is not a general coding agent.

## Copy the package

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview `
  --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview
Set-Location Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview
.\run_wrench.ps1
```

The package is a Hugging Face Safetensors directory with tokenizer, bundled
verifier, deterministic toolbelt, context policy, and a model-local server.
It accepts Ollama-shaped `/api/chat` and `/api/generate` requests, including
`options.num_ctx=4000000`, without an external gateway.

## Connect Claude Code locally

The package also includes a local Claude Code launcher. It starts the Wrench
Anthropic-compatible `/v1/messages` endpoint, uses a fresh Claude config by
default, and points external proxy variables at a local fail-closed blocker.
The Wrench loopback endpoint is excluded from that blocker, so the run either
uses this package or fails instead of silently reaching a first-party provider:

```powershell
.\run_claude_code.ps1 -Print -Prompt "Read README.md and report its first heading."
```

The default launcher allows only `Read`, `Glob`, and `Grep`. Pass explicit
Claude Code arguments when a different local permission policy is required:

```powershell
.\run_claude_code.ps1 -Print -AllowedTools Read,Edit -Prompt "Inspect the project and propose a bounded change."
```

This is a local integration path, not a claim of Claude model ownership,
MiniMax parity, or production readiness. Wrench remains bounded by its own
verifier and has no direct mutation authority.

## Connect OpenCode and DeepSeek Harness

Start the package server in one terminal:

```powershell
.\run_wrench.ps1
```

In the project directory, copy `opencode.wrench.json` to the client config
name `opencode.json`, then run:

```powershell
opencode run --pure -m wrench/wrench-local "Read README.md and report its first heading."
```

For DeepSeek Harness, set the local-only key and apply the bundled overlay:

```powershell
$env:WRENCH_LOCAL_API_KEY = "wrench-local"
dsh --profile headless --patch .\dsh-wrench.patch.yml "Read README.md and report its first heading."
```

Both configs declare the package's 4,000,000-token raw input surface. The
Wrench server receives the complete request and applies its deterministic
first-layer reducer. The client integrations are local smoke paths and do not
claim dense native attention quality or production readiness.

## What the 4M claim means

The production-value path is hybrid and model-local:

1. receive the complete raw payload directly at the package endpoint;
2. use deterministic MapReduce, bounded search, AST/dependency extraction,
   and exact lookup windows to identify useful evidence;
3. keep recent intent hot and old material reference-only;
4. compact model work to a bounded effective context, normally 64K;
5. run the bounded proposal, verifier, and identical stronger-model fallback.

The first-layer receipt records selected and omitted spans, raw payload hash,
effective working context, route source, and gate latency. Dense native 2M/4M
attention is optional research. It is not the Wrench product claim.

When the optional dense-native lane is enabled, `-NativeDirectInput` enables
the first-layer gate automatically. `-DenseNativeGate` can also be supplied
explicitly. The raw request still arrives at the model-local native
endpoint, but the package's first model-side stage compacts it to 32K to 64K
before expensive attention:

```powershell
.\serve_freetoken.ps1 -OllamaApi -NativeDirectInput -DenseNativeGate
```

The gate is fail-closed and records the raw payload hash, selected working
context, and gate stage. `-BypassDenseNativeGate` is reserved for separate
reducer-bypassed native capacity probes and cannot be combined with a
dense-native mode switch.

## Run the model-local endpoint

```powershell
python .\wrench_server.py --model-dir . --allowed-root . --mechanical-only
```

The endpoint is `http://127.0.0.1:28900/v1/chat/completions`. The same process
also exposes `/api/tags`, `/api/show`, `/api/chat`, and `/api/generate` for
clients that expect an Ollama-shaped surface. It receives the full raw
conversation directly and emits hash-bound context-gate receipts.

## Backend support matrix

| Surface | Current status | Boundary |
| --- | --- | --- |
| Bundled model-local server | Verified | Accepts about 4M raw tokens and reduces to a bounded working context. |
| Ollama-shaped `/api/*` surface | Verified | Package-local compatibility API, not stock Ollama native generation. |
| OpenCode, DeepSeek Harness, Claude Code | Verified | Read-only local client smoke completed with zero model calls. |
| Stock Ollama native runner on Windows | Not verified | Ollama `0.34.2` still cannot run the MLX quantizer on Windows; both current NVFP4 import and BF16→NVFP4 conversion fail before a usable native model is created. |
| vLLM | Not verified | Requires a registered Wrench architecture and staged-prefill adapter. |
| GGUF / llama.cpp | Not verified | Do not use a conversion that silently drops the Wrench retrieval runtime. |

The current package-local evidence is recorded in phases 350 through 365 in
the source repository. The supported portable path is the bundled server and
its local client templates. The stock Ollama import and runtime boundaries are
recorded in phases 366 and 367.

The `--mechanical-only` mode is the verified fast path. Remove it only when a
compatible local native backend is available for ambiguous requests. Native
generation is separately verified and must not be inferred from the API shape.

Important loader boundary: this Experimental Preview contains ModelOpt NVFP4
packed tensors. Transformers 5.17.0 can verify the config and tokenizer, but
ordinary `AutoModel.from_pretrained()` cannot restore these packed weights. Use
the bundled `serve_freetoken.ps1` launcher with a compatible FreeToken ModelOpt
runtime for native loading. The package also includes
`verify_freetoken_backend.py`, which records full-weight load, 4M KV-capacity
configuration, a small generation smoke, and the 10% RAM/VRAM reserve check.

The embedded worker API is also available directly from the downloaded
directory:

```python
from wrench_worker import WrenchWorker

worker = WrenchWorker.from_pretrained(
    "./Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview", load_model=False
)
result = worker.propose([
    {"role": "user", "content": "Read README.md with a 65536 byte limit."}
])
```

## Current evidence

On the current-package 220-case diagnostic replay, with client-side mechanical
shortcut disabled:

- cases: `220/220`, including `120` eligible rows;
- Wrench plus identical MiniMax fallback weighted final success: `100%`;
- Wrench plus identical MiniMax fallback frontier tokens: `0`, local tokens: `24,141`;
- median / p95 latency: `184.804 ms` / `297.676 ms`;
- prohibited accepts: `0`;
- unexpected mutations: `0`.

The current release-candidate package-local 4M probe accepted `3,999,995` raw
estimated tokens and completed in `172.585 ms`, including `23.772 ms` of
context-gate time. It compacted to a bounded `64,000`-token working budget and
made zero model calls. The 2M/4M retrieval probe passed all `6/6` needle
placements. These are direct raw intake and bounded MapReduce diagnostics, not
native dense decoder quality.

These are hybrid model-local diagnostics, not dense native attention quality,
stock Ollama native generation quality, family-disjoint approval, or
production enablement. The current stock Ollama native import and quantizer
boundaries are explicitly recorded as failed on the Windows validation host in
phases 366 through 368. GGUF and vLLM require architecture adapters and are
not claimed as verified.

## Development status

The full source regression is `202 passed, 0 failed`. Final release still
requires the human-approved family-disjoint MiniMax-worker trace set,
independent RTX 5060 Ti verification, and operational shadow evidence. Wrench has no direct
mutation authority. It proposes bounded actions or abstains, and the
surrounding verifier must enforce execution policy.
