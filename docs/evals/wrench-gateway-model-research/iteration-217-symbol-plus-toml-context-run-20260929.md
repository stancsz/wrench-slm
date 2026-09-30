# Iteration 217: symbol retrieval plus exact TOML table

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER217-SYMBOL-TOML-20260929-01`  
Nonce: `f9517cc4-cc28-4f8b-a327-94eb157b9116`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`  
Heartbeat-declared gateway goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch still open)

## Outcome

Both arms completed in one attempt and passed the AST allowlist and all six deterministic behavior checks. This is the same repeatedly used authored synthetic retry-function task, so it is an exploratory integration result, not an independent task, held-out outcome, success-rate estimate, or all-day engineering evidence.

| Arm | Actual input IDs | Output IDs | Full-lifecycle local tokens | Generation seconds | Verified |
|---|---:|---:|---:|---:|---|
| Full five-file context | 8,805 | 85 | 8,890 | 39.3978 | Yes |
| Wrench exact symbol + TOML table | 301 | 85 | 386 | 31.7963 | Yes |

Actual prompt-input reduction: **96.5815%**. Input-plus-output **local-model tokenizer** reduction: **95.6580%**. This is the highest full-lifecycle local-token reduction in the current paired code-task demo sequence, 58 tokens better than Iteration 216. It clears a 95% local proxy on this single known task; it is not Frontier-token usage or billed savings. Frontier calls: 0. Provider tokens/savings, local energy, and all-in cost: null. No retries or recovery fetches.

The context receipt contains exactly these two selected source references and no whole-file source:

- `src/retry.py`: `symbol`, `parser_reported_exact`, lines 14-16, parser `python_ast`, source SHA-256 `7485fbc3671617dd5d0bab363223fd3f7de358bde206739806686a994e91062a`.
- `config/service.toml`: `configuration_table`, `parser_reported_exact_table`, lines 7-13, parser `tomllib-table-v1`, source SHA-256 `2ae3e968de8956a2087132a0b2147cad558b44783c620ee199456828496ae588`.

Required evidence remains visible: the complete requested function and cap value `max_backoff_ms = 4000`. The unrelated `[auth]` configuration table is excluded by the tested regression.

The 419/299 helper counts and its 28.6396% source-local input reduction are only a two-source compiler diagnostic. The registered cross-arm comparison is the outer actual generation count (8,805 versus 301 input IDs); do not conflate the two denominators.

## Implementation and regression

The experiment exposed and fixed two gaps: symbol-targeted requests previously skipped TOML candidate creation, and the localized-symbol branch removed the required TOML whole file before it had added table-span candidates. The bounded API now accepts a separate TOML retrieval query; it adds parser-validated table segments, preserves exact source lineage, and excludes the whole file unless explicitly preserved or independently required by source identity. The helper's additional required-path and TOML query inputs are optional, validated, and leave default callers unchanged.

Focused test `test_symbol_targeted_query_can_also_select_required_toml_table_span` passed (`1 passed in 0.87s`) under the repository `.venv`. It confirms source plus table evidence, exact parser/source refs, required code/config content, and absence of unrelated secret config. The model integration pair independently verifies the final generated function.

## Identity and limits

- Protocol `docs/evals/wrench-gateway-model-research/iteration-217-symbol-plus-toml-context-protocol-20260929.md`, SHA-256 `16c15534f17e22c4723d087cd63e6ccca0c277c07dd828462120c195346f9f6b`.
- Runner `examples/gateway_context_mvp/run_code_task_local_mvp_iter217.py`, SHA-256 `22f28ea22f7f3e362e0b692ee647a63f94ab34ed2e47fe5204892571d1728f3e`.
- Context helper `examples/gateway_context_mvp/run_local_model_mvp.py`, SHA-256 `ba7ac0ace987f3dfe0b995055791a04ba9eca566232ecf1f6423917c96a959af`.
- E0 pipeline `src/wrench_harness/e0_context_pipeline.py`, SHA-256 `b62d5fcd7232d9f639bad4c9255404e529e2f8b57cfb43b0bfed52549a889822`. Focused test file SHA-256 `47ef644c52627866abadd39dfd712a837449bcbebb37f2a9df04482ae0d5d351`.
- Receipt `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\code-task-iter217-qwen35-4b.json`, 10,918 bytes, SHA-256 `5727f5547687b5513f5a7acb72d95bab6b67f52e4a1e2e02ed644a8c5d30ca9c`. Fixture SHA-256 `92debc627977cf5370e51a52943442f816c293984cc991a9cf3fae661f055be1`; context snapshot SHA-256 `393760eb75f4e9aae491931f80f3fda6d38f21cb54f9835d30fb639efd5f862d`.
- Model `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base, no adapter, 14 files totaling 9,342,907,469 bytes. Runtime 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2; NVIDIA GeForce RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`. Load 30.1869s; total 102.0070s. Peak CUDA allocated/reserved 11,590,978,048/11,916,017,664 bytes.
- 183 samples; minimum free RAM 19.4030%, VRAM 22.6642%; no reserve breach or monitor error.
- Python socket connects blocked, not OS-level isolation. No provider/SubRoute, credentials, held-out data, real-repository writes, or LoRA activation.
- Storage job reserved 100,000,000 bytes. Receipt and report were counted before releasing the reservation; final aggregate checker status was below the 50 GB cap, and C: free space was far above 5 GiB.

## Decision

This pair shows that exact symbol targeting plus the separately queried exact TOML table can preserve this synthetic task with 386 local tokens and reduce the full-context local tokenizer count by 95.66%. Next, test on a frozen, diverse task set and a frozen retrieval policy; do not tune query strings per final episode. Continue measuring Frontier usage/cost and task failures before making a product claim. Model size winner, Wrench LoRA value, Frontier 95/5/95 gates, all-in cost, and reliable all-day engineering remain unproven.
