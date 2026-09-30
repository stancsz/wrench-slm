# Iteration 168: Qwen3.5-4B dev evaluator source review

- Assignment: `WRENCH-QWEN35-4B-DEV-EVAL-REVIEW-ITER168-20260929`
- Nonce: `5dc062f2-17f3-4e0a-9c16-b24078793363`
- Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (matches expected)
- Verdict: **HOLD. Do not admit preflight or dev inference from this package.**
- Scope: static source and protocol review only. This report is not a storage/resource admission or execution approval.

## Findings

### P1. Reference and assistant labels are parsed before predictions are sealed

`load_dev_payload()` calls `json.loads(line)` on each complete labeled dev row before either model arm runs. JSON decoding materializes the full assistant message and `gold` object in process memory. The runner also inspects all three message roles and checks every message content type, including the assistant content, then projects `messages[:2]` for model input. The model prompt is therefore answer-blind, and I found no path passing the assistant response or `gold` into generation. However, the stronger declared boundary that reference/assistant labels remain untouched until prediction sealing is false. The later call to `read_dev_references()` does not make this an untouched-reference run. Keep the run on HOLD until source and protocol accurately enforce or describe the intended boundary. A strict boundary needs selective parsing that never materializes target/reference fields before prediction files are sealed.

### P2. Output path confinement is checked after paths have already been written

The runner creates output/log directories and writes `resources.jsonl` with ordinary `Path.mkdir`/`write_bytes` before `check_output_budget()` verifies that `ARTIFACTS` and `LOGS` resolve below the approved root. `SCRATCH_PARENT` is likewise created through ordinary path operations; the pinned-tree helper checks scratch only when the monitor later samples it. A pre-existing junction or a path race can redirect initial writes before these later checks reject the path. The bounded storage reservation and output caps do not make these writes path-confined. Add reparse-safe parent creation/opening and verify the final path before the first write; retain checks against races while the job runs.

### P2. The 300-second generation limit is not an independent hard timeout

`generate()` passes `max_time=300` to `model.generate()` and classifies elapsed time after it returns. There is no separate per-generation watchdog/process timeout. This is a library stopping criterion, not an independently enforced wall-clock kill boundary. The resource monitor can interrupt on RAM/VRAM/scratch breach, but not on generation duration. Treat long generations as unbounded if `generate()` fails to return; add a supervised hard timeout before relying on the protocol's timeout claim.

### P2. Preflight receipt validation does not check every identity claimed by the protocol

`score-dev` verifies the preflight evaluator/protocol hashes, fit manifest, inventory, dev and chat-template hashes, prediction file hashes, and resource log hash. It does not validate the preflight receipt's model ID/revision, config and dataset-manifest hashes, runtime package/Python identity, GPU name, or reservation hash against the expected values, despite the protocol saying the preflight must match the same base, data, runtime, and GPU. The output receipt is a local JSON file without an authenticity mechanism. Bind and validate those fields (and validate the exact resource identity) before treating a preflight receipt as a gate.

## Positive controls observed

- Base and adapter arms use the same loaded adapted model; the base arm enters `disable_adapter()` and the LoRA arm enables it. Generation receives only the projected system/user messages.
- The runner pins HEAD, scorer/protocol/trainer/helper hashes, model inventory/config, fit manifest/resources/epochs, adapter files, dev payload, and chat template. It loads local model/adapter paths with `local_files_only=True`, `trust_remote_code=False`, and offline Hugging Face flags.
- I found no provider client, credential read, SubRoute endpoint, Frontier call, activation operation, tool execution, shell authority, code mutation, or held-out path access in the assigned scorer. Local tokenizer counts are correctly labelled as not provider usage or savings.
- It samples RAM/VRAM, checks a job reservation and destination free space, caps scratch/output sizes, checks model/adapter tree identities, retains failures, and scores exact decisions with denominators and Wilson intervals. These controls do not remedy the findings above.
- The package is a synthetic dev diagnostic only. Even a perfect score would not prove engineering utility, paid token savings, the 95/5/95 targets, or all-day operation.

## Hashes and commands

Hashes were checked before and after review. Both package hashes match the assignment exactly:

| File | SHA-256 before | SHA-256 after |
|---|---|---|
| `tools/score_gateway_lora_screen_03_4b_dev.py` | `F15D9950FD5A4A9EE66D327AD531CA92B026A226A19A90466D73643EF946623A` | same |
| `docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md` | `94188636ED51E603DA73BE661B356E870F39107FEE41CB1D1D030618644DD677` | same |

Other reviewed identities: fit report `869401EE87031577F663E9C9C052C35BFA4BD7E98786A4806077B4F82459E04B`; trainer `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5`; training protocol `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893`; pinned-tree helper `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499`.

Commands used: `git rev-parse HEAD`; `Get-FileHash -Algorithm SHA256` on assigned files; bounded `Get-Content` on scorer, protocol, and pinned-tree helper; `rg -n` on assigned files for label access, paths, resources, timeout, identity, and external-call patterns. No Python, tests, AST checks, model/runtime imports, inference, training, benchmark, tokenizer, network, or held-out reads were run. No model job or resource workload was started. Report size is under 15 KB.
