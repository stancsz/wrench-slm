# Iteration 209: Local code-task MVP, first verifier version

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER209-20260929-01`  
Nonce: `0732543c-0bda-4d48-8d85-2cd14bc86c30`  
Repo HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Identity and scope

- On-disk active gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`.
- The 2026-09-29 heartbeat supplied `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` as the active goal hash. It does not match the current goal file. This iteration bound itself to the file actually read and did not edit the goal. Reconcile this discrepancy before any hash-bound training package review.
- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter209.py`, SHA-256 `491F0E08131447A5575D6C06F0DE011D016FF0040EE07C8F7C7BA37347DCBAA8`.
- Focused verifier tests: `tests/test_gateway_code_task_verifier.py`, SHA-256 `8F331E8F58AA5A80D51C4D3BE87376BFAA24BCADCC7C53C90A412DB9025C8B4C`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\code-task-iter209-qwen35-4b.json`, 12,736 bytes, SHA-256 `3808CE36191483EBCC3FF3140C981E28E6A962130D4787363E45EEDB761DC06B`.

The task asked Qwen3.5-4B to propose a replacement for a synthetic retry-delay function that honors `max_backoff_ms`. The full-context and Wrench-prepared arms used the same frozen fixture and model. The Wrench arm retained the required function and TOML configuration evidence. A structural allowlist preceded execution of generated code, which ran six fixed behavioral checks. One verifier failure received one retry; Wrench retried with a full-context recovery fetch. The task only ran locally, with Python socket connects blocked and model/runtime offline. No repository files were modified by the model.

## Result

- Context preparation passed and preserved all three required quotes.
- Initial local Qwen tokenizer input: full context 8,805 tokens; Wrench context 596 tokens, a 93.2311% initial input reduction.
- The run made four local generations, one retry per arm. Including retries and outputs, full-context used 17,793 local tokens and Wrench used 9,579, a 46.1642% local full-lifecycle reduction for this run. These are local model tokens, not Frontier tokens or billed savings.
- Strict verifier v1 marked both arms unsuccessful. The full-context first output was fenced and truncated at the token limit; the retry had a negative-attempt behavior defect. The Wrench first output was a plausible function with a docstring and local variable, but verifier v1 rejected that valid structure before running behavioral cases. Its recovery retry also failed the negative-attempt behavior case. Retain all raw outputs in the receipt.
- Verified success retention is undefined because the baseline did not pass. No quality or 95% savings claim follows from these data.

## Runtime and checks

- Model: pinned `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16, base only. The trained LoRA stayed inactive. This tests a possible local code-worker role, not the provisional 2B bounded-controller lead.
- Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0; NVIDIA RTX 5060 Ti.
- Model load: 30.3348 seconds; total: 166.0399 seconds; peak CUDA allocated/reserved: 11,616,028,672 / 13,071,548,416 bytes.
- Minimum sampled RAM free: 19.31%; minimum VRAM free: 15.54% (2,534 MiB); 229 resource samples. The 10% runtime floors were maintained.
- Two focused verifier tests passed through direct Python invocation; `git diff --check` passed with line-ending warnings on pre-existing dirty files. The ordinary pytest command was not used.
- Storage stayed under the 50 GB cap; the 150,000,000-byte job reservation is released after this report and receipt are counted.

## Disposition

This is a useful first local code-task integration attempt, but it failed the authored task and exposed an over-restrictive verifier grammar. Preserve this v1 receipt unchanged. A separate iteration may broaden the verifier to accept safe docstrings, annotations, local assignments, and a single optional Python code fence while keeping a restrictive AST allowlist and the same behavioral cases. Re-run with a new protocol, job, nonce, and receipt; report both the original and corrected protocol results. Do not describe the correction as a model gain. The MVP remains far from representative engineering, all-day reliability, and the paired Frontier acceptance gates.
