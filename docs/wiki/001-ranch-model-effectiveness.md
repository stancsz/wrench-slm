# 001 - How effective is the current RANCH model right now?

- **scope:** Current Wrench-SLM/Wrench-Pro V21 LoRA adapter in this checkout, verified on 2026-09-10 with direct packaged inference on Windows 11 and an RTX 5070 Ti. This covers authored developer-tool scenarios and fresh V8 challenge data. It excludes hosted serving, router economics, production traffic, CPU or Raspberry Pi performance, and arbitrary shell execution.
- **status:** draft
- **verified:** 2026-09-10
- **decision it feeds:** Whether the current model is useful enough to move from a narrow local proposal layer toward a matched router or production pilot.

## Answer

The repository has no exact `RANCH` identifier, so this review treats “RANCH” as the current Wrench-SLM/Wrench-Pro V21 artifact. V21 is effective as a narrow, read-oriented structured tool-call proposer. It is not yet proven as a production agent, router, or cloud-cost-saving system.

The strongest current model-quality estimate is the fresh V8 evaluation: 502/506 exact across the separately authored challenge and sealed suites, or 99.21% with a descriptive Wilson 95% interval of 97.99% to 99.69%. The routine slice was 276/280, or 98.57%; fallback behavior was 184/184. The four misses were three safe abstentions on routine line-read or draft tasks and one invalid tool prediction on a Chinese configuration task that the validator converted to fallback. No fixture filesystem changes occurred. This is strong evidence for the declared task contract, not a universal accuracy estimate.

The internal V21 suites remain perfect at 440/440 and 220/220, but they are authored around the same narrow contract. The fresh V8 run is more probative because its generator, wording families, paths, and values were separate from V21's release data.

Prediction latency is real but limited: the fresh 440-case run measured 1.133 seconds p50, 3.441 seconds p95, and 3.630 seconds p99 on one Windows 11 RTX 5070 Ti setup. Peak CUDA allocation was about 1.12 GB and reserved memory about 1.25 GB. There is no concurrency, CPU, Raspberry Pi, hosted-service, cold-start, or end-to-end cloud comparison behind these numbers.

The model's safety boundary is honest but narrow. The packaged runtime proposes a call and validates it; it does not execute the generated tool. The current Pro path uses unconstrained generation followed by strict validation, while the FSM and grammar code are separate paths. This gives useful rejection behavior, but it is not grammar-constrained generation and does not prove correct semantics or safe handling of arbitrary commands. The repository still lacks a measured replay of the broader mutation subset.

The usefulness question is still open. The matched cloud comparison was stopped because the gateway returned a different model than requested and accounting became incomplete. No final comparison report exists, so there is currently no evidence for cloud-token reduction, end-to-end speedup, or net workflow benefit.

External benchmark work supports this caution. BFCL evaluates real-world function-calling data across single-turn, multi-turn, parallel, executable, and agentic categories. ToolSandbox evaluates stateful conversations with implicit tool dependencies, minefields, and an average of 13.9 turns and 3.8 tool calls per case. WildToolBench reports that no evaluated model exceeded 15% session accuracy on its more natural “wild” user behavior. ToolBench-X shows that agents that perform well with reliable tools can fail when tools have recoverable specification, invocation, execution, output, or cross-source hazards. V21 has not been tested on those dimensions.

## Bottom line

Use V21 as a bounded local proposal and abstention component behind a strict validator. Do not describe it as production-ready, as a measured latency or cost win, or as a general tool-using agent. The next decisive experiment is a fresh matched workflow comparison with a fixed or explicitly characterized cloud route, real tool observations, all failures retained, and measured cost and latency at the intended concurrency.

## Receipts

- V21's declared scope, authored-data limits, and internal results: [README](../../README.md), [model card](../../releases/v21/MODEL_CARD.md), [data card](../../releases/v21/DATA_CARD.md), and [evaluation report](../../releases/v21/EVALUATION_REPORT.md); confidence: high for the release-scope description.
- Fresh V8 challenge result, 66/66 exact: `artifacts/model-release/v21-package-independent-challenge-v8/summary.json` and `run.json`; confidence: high for this run and dataset.
- Fresh V8 sealed result, 436/440 exact, 276/280 routine, 160/160 fallback: `artifacts/model-release/v21-package-release-authoring-v8/summary.json`, `run.json`, and `predictions.jsonl`; confidence: high for this run and dataset.
- The four fresh sealed failures are visible in `predictions.jsonl`: three `model_abstention` rows and one `argument_keys` invalid prediction; confidence: high.
- The usefulness comparison stopped without a verdict because model routing and accounting were invalid: [pilot progress](../../docs/reference/USEFULNESS_PILOT_PROGRESS.md); confidence: high.
- The production readiness audit leaves hosted reliability, router savings, concurrency, arbitrary shell safety, and mutation replay open: [production readiness audit](../../docs/reference/PRODUCTION_READINESS.md); confidence: high.
- The packaged path is unconstrained generation followed by validation: [pilot inference](../../wrench/pilot_inference.py) and [engineering techniques assessment](../../docs/reference/AI_ENGINEERING_TECHNIQUES.md); confidence: high.
- BFCL describes a real-world, periodically updated function-calling benchmark with single-turn, multi-turn, and agentic evaluation: [BFCL V4](https://gorilla.cs.berkeley.edu/leaderboard.html), accessed 2026-09-10; confidence: high.
- ToolSandbox evaluates stateful, conversational, interactive tool use and reports 1,032 cases, 13.9 average turns, and 3.8 average tool calls: [ToolSandbox paper](https://arxiv.org/abs/2408.04682), published 2024-08-08; confidence: high.
- WildToolBench reports no model above 15% session accuracy on its wild user-behavior benchmark: [WildToolBench paper](https://arxiv.org/abs/2604.06185), published 2026-02-13; confidence: medium, because it is not directly comparable to V21's narrow task distribution.
- ToolBench-X reports reliability gaps under recoverable tool-environment hazards and argues for task-completion evaluation beyond function-call accuracy: [ToolBench-X paper](https://arxiv.org/abs/2606.25819), published 2026-06-24; confidence: medium-high.

## Changelog

- 2026-09-10: created from current V21 receipts, fresh V8 reruns, scoped test results, and external tool-use benchmark research.
