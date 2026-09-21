# Wrench SLM

> **还在让 Astra、Fable、Sol 搬砖？别给体力活付天才价。Wrench 接下 4M tokens 原文：历史回放推理费减少 94.8895%；较新版本回放同组 120 项搬砖任务，云端调用费直接归零。**<br>
> **Still paying Astra, Fable, or Sol to do grunt work? Stop paying genius rates for busywork. Wrench takes in 4M tokens of raw input: 94.8895% lower inference costs in a historical replay. A newer version replayed the same 120 routine tasks with zero cloud API spend.**

费用按 [MiniMax 上游计费记录](phases/phase-185-v2-teacher-capture/teacher-220-v2-max1024.json)与 [v88 配对回放](phases/phase-215-v88-220-replay-v2/trace-manifest.json)逐项核算，覆盖 120 项 eligible 任务，包含 5 次回退。较新的 [v103 回放](phases/phase-261-v103-220-replay/trace-manifest.json)中，这 120 项的云端调用为 0，正确结果为 119/120。仅计这组任务的云端推理费，本地硬件和电费尚未计价；未实测 Astra、Fable、Sol 的账单。

Costs are reconstructed per task from the linked MiniMax provider usage and v88 paired replay, covering 120 eligible tasks and five fallbacks. The newer v103 replay made zero cloud calls on those 120 tasks, with 119/120 correct outcomes. Figures cover cloud inference for this task set only; local hardware and electricity remain unpriced. Astra, Fable, and Sol bills were not measured.

Wrench is a bounded developer-tool execution SLM for fast, repetitive,
verifiable mechanical work. It proposes structured actions or abstains. An
independent verifier and the stronger-model fallback retain final authority.
Wrench never executes arbitrary shell commands, uses credentials, or writes
autonomously.

## Copy-paste model package

The current experimental preview Hugging Face artifact is:

`stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview`

```powershell
hf download stancsz/Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview `
  --local-dir Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview
Set-Location Wrench-4B-Qwen3.6-8E-NVFP4-native4M-v97-dense-native-gate-Experimental-Preview
.\run_wrench.ps1
```

This is an **Experimental Preview**. It is not for production deployment,
safety-critical use, or treating benchmark results as production validation.
Run it only in an isolated, non-production environment.

The package is a Hugging Face Safetensors directory with tokenizer, bundled
verifier, deterministic toolbelt, context policy, and a model-local server.
It accepts Ollama-shaped `/api/chat` and `/api/generate` requests, including
`options.num_ctx=4000000`, without an external gateway.

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

If a dense-native lane is enabled later, this is an explicit model/runtime
requirement: the portable package must include a fast first model-side pruner
and cherrypicker. It must inspect the complete raw sequence and compact it to a
bounded 32K to 64K active working context before expensive attention runs. A
gateway-only reducer or a metadata-only context setting does not satisfy this
target.

## Real harness integration

The model-local endpoint now has verified local smoke paths for OpenCode,
Claude Code, and DeepSeek Harness. OpenCode uses OpenAI-compatible tool calls,
Claude Code uses Anthropic `tool_use` and `tool_result`, and DeepSeek Harness
uses an isolated headless profile. Each path performed a real read-only file
operation, returned one bounded Wrench proposal, and settled without a model
call or repeated tool loop. See
`phases/phase-238-real-harness-integration/receipt.json`.

## Current v97 evidence

The current portable runtime is below the 4.25B parameter ceiling at
`3,881,244,016` verified parameters.

On the historical 220-case diagnostic replay, with client-side mechanical
shortcut disabled:

- weighted mechanical frontier-token coverage: `94.5411%`;
- net frontier-token savings: `95.5310%`;
- Wrench plus identical MiniMax fallback final success: `99.6503%`;
- median / p95 latency: `183.314 ms` / `337.174 ms`;
- prohibited accepts: `0`;
- unexpected mutations: `0`.

The direct model-local context matrix passed three repetitions each at 64K,
128K, 256K, 2M, and 4M. At 4M, the measured raw estimate was `3,999,995`
tokens and complete HTTP p50/p95 was `158.906` / `159.251 ms`. The 2M/4M
reference-lookup probe recovered exact proposals in `18/18` cases, with 4M
retrieval p50/p95 of `32.560` / `40.772 ms` and zero model calls.

These are hybrid model-local diagnostics, not dense native attention quality,
stock Ollama native generation quality, family-disjoint approval, or
production enablement. The current stock Ollama native generation boundary is
explicitly recorded as failed on the validation host. GGUF and vLLM require
architecture adapters and are not claimed as verified.

## Development status

The repository contract and evidence live in [GOAL.md](GOAL.md). The latest
receipts are under `phases/phase-230-current-source-matched-arms-v2`,
`phases/phase-236-portable-package-http-4m`, and
`phases/phase-238-real-harness-integration`.

The full source regression is `182 passed, 18 warnings`. Final release still
requires the human-approved family-disjoint MiniMax-worker trace set,
independent RTX 5060 Ti verification, and operational shadow evidence.
