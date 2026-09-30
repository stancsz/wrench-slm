# Iteration 217 protocol: symbol retrieval plus exact TOML table

Date: 2026-09-29 (America/Edmonton)
Job: `WRENCH-CODETASK-MVP-ITER217-SYMBOL-TOML-20260929-01`
Nonce: `f9517cc4-cc28-4f8b-a327-94eb157b9116`
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`
Heartbeat-declared goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (mismatch recorded; no training)

## Question

Can Wrench prepare only the exact requested Python function and the relevant TOML table in one symbol-targeted request, retaining both required pieces with source hashes and exact parser spans while omitting the whole source files and unrelated config? If so, does the unchanged local code-generation prompt still pass the same deterministic verifier, and what are the actual paired generation token counts?

The symbol identifier comes directly from the unchanged task request. A distinct TOML evidence query (`retry initial_backoff_ms max_backoff_ms`) comes from the requested behavior/config names, not from expected output. This is a focused development ablation of the same previously reused synthetic task; not an independent or held-out episode and not a general coding success estimate.

## Change and exact identities

- Runner `examples/gateway_context_mvp/run_code_task_local_mvp_iter217.py`, SHA-256 `22f28ea22f7f3e362e0b692ee647a63f94ab34ed2e47fe5204892571d1728f3e`.
- Context helper `examples/gateway_context_mvp/run_local_model_mvp.py`, SHA-256 `ba7ac0ace987f3dfe0b995055791a04ba9eca566232ecf1f6423917c96a959af`. Adds a validated optional TOML-specific retrieval query.
- Pipeline `src/wrench_harness/e0_context_pipeline.py`, SHA-256 `b62d5fcd7232d9f639bad4c9255404e529e2f8b57cfb43b0bfed52549a889822`. When a symbol query is used, an explicit TOML query may drive required config-span extraction; the localized-symbol branch adds exact TOML spans and excludes their whole-file source unless explicitly preserved/required by source identity. Default pipeline callers remain unchanged.
- Focused regression `tests/test_e0_context_pipeline.py`, SHA-256 `47ef644c52627866abadd39dfd712a837449bcbebb37f2a9df04482ae0d5d351`; `test_symbol_targeted_query_can_also_select_required_toml_table_span` passed under the repository `.venv` after implementation.
- Full-context baseline remains all five fixture files. Wrench requires `src/retry.py` and `config/service.toml`, queries `symbol:calculate_retry_delay`, sets the independent TOML query above, and enables symbol/table spans. All task wording, system/user prompts, model, decode cap, verifier, retry/recovery, and resource rules remain unchanged from Iter216.
- Verify reference kinds include only exact Python symbol and TOML table spans, no whole-file ref; exact function body and configured cap are present; unrelated `[auth]` is absent. If any gate fails, preserve the failure.
- Model: pinned `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 base only, no LoRA. Compare actual outer generation input/output IDs and full lifecycle local tokens. Helper source-local token estimates are diagnostics only.

## Admission and safety

Output is no-clobber at `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\code-task-iter217-qwen35-4b.json`. Unique 100,000,000-byte storage reservation for this job includes the repository, approved data root, Docker WSL model volume, and automation directory. Before and during inference require >=10% free RAM and VRAM and >=5 GiB free on C:. Use the in-process sampler and independent pre/post GPU check. Load the exact model locally/offline and keep Python socket connects blocked (not OS-level isolation). Do not call provider/SubRoute, read credentials, touch real repositories, or open held-out data. Keep any adapter inactive. Release reservation only after the process stops and receipt/report bytes are counted.

This one reused synthetic result cannot prove the 95/5/95 Frontier targets, all-in cost, best model, LoRA contribution, or all-day engineering.
