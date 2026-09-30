# Iteration 210: corrected local code-task verifier protocol

Date: 2026-09-29 (America/Edmonton)  
Job: `WRENCH-CODETASK-MVP-ITER210-20260929-01`  
Nonce: `84c0d731-0718-4c9e-b1b7-4da1059c1d53`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Why this iteration exists

Iteration 209 saved a complete paired local run, but its verifier rejected normal safe Python output containing an optional code fence, a docstring, type annotations, and one local assignment. Its raw outputs are preserved in `code-task-iter209-qwen35-4b.json` and its report. This iteration corrects that verifier grammar without changing the synthetic task or six behavioral cases. It is a verifier correction, not a model improvement, and the repeated single task is not an independent sample.

## Exact package

- Runner: `examples/gateway_context_mvp/run_code_task_local_mvp_iter210.py`, SHA-256 `0C0D0828DFD85DBA731B6C185A514925761CB4167A1714B2F5B1693B47F48A35`.
- Focused tests: `tests/test_gateway_code_task_verifier_iter210.py`, SHA-256 `70913467E5C28D4D4EE6DCA71F7EB7BC6C24012F00D1CCF33220ADE1F7462DC8`.
- Expected output, created once with no-clobber: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\code-task-iter210-qwen35-4b.json`.
- Base: `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, exact local inventory and snapshot checks reused from the Iteration 207 runner. BF16 base only; no adapter activation.
- Runtime: pinned Iteration 206 Python 3.13.15, Torch 2.14.0+cu132, Transformers 5.17.0, CUDA 13.2, and RTX 5060 Ti UUID `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`.

## Verifier v2

Accept exactly one function with the required name and three arguments, optional `int` annotations, an optional single outer `python` code fence, an optional string docstring, and either a single return or one `delay` assignment plus a return. The AST allowlist permits only the fixed names and `min`/`max` calls; it rejects imports, attributes, loops, file/process access, extra functions, decorators, and unsupported syntax. Execute only after the AST contract passes, with builtins removed and only `min` and `max` supplied. Verify negative, zero, ordinary, over-cap, and changed-cap values against the TOML fixture. Test both the corrected examples and the actual Iteration 209 saved outputs; the negative-attempt defect in the Iteration 209 retry must still fail.

## Paired local procedure

Prepare both prompts from the same five-file synthetic snapshot and task. Compare full fixture context against deterministic Wrench compact evidence. Load the model once, run greedy decoding with a 160-token cap, alternate which prompt arm goes first by fixed nonce, and allow at most one retry per arm after a verification failure. A failed Wrench attempt fetches full immutable fixture context before retry; the full-context arm retries with the same evidence plus a verifier correction. Record every raw answer, attempt, retry/recovery action, exact model input/output token counts, prompt and snapshot hashes, verified cases, latency, peak CUDA memory, and sampled RAM/VRAM. If either resource floor reaches 10%, stop and preserve a failure receipt.

The script forces local offline mode and blocks Python socket connects. It makes no Frontier/SubRoute/provider calls, does not access held-out data, and cannot modify the real repository. Local Qwen tokenizer counts are not provider usage or billed savings. The one task is not representative coding effectiveness or all-day engineering evidence.

## Admission and disposition

Before launch, require a fresh storage status and the unique 150,000,000-byte Iteration 210 reservation (already active), at least 5 GiB free on C:, exact runner/test/goal/HEAD identities, no existing output or duplicate Iteration 210 process, and at least 10% free RAM and VRAM. Keep the 10% reserve during the run. Release the reservation only after the process stops and the receipt and report are counted. Keep Iteration 209 immutable and report both protocol outcomes.

The current goal file SHA differs from the heartbeat's stated `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027`. This protocol pins the actual on-disk file and records the discrepancy. No training or held-out evaluation is authorized by this protocol.
