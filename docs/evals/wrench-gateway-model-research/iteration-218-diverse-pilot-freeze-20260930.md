# Iteration 218: freeze the diverse local code-task pilot

Date: 2026-09-29 (America/Edmonton)  
Protocol job: `WRENCH-CODETASK-ITER218-FREEZE-20260930-01`  
Nonce: `c5ec7501-cc7c-42b2-bd21-a0d61d497216`  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
On-disk gateway goal SHA-256: `2fb13f31d4b6d528a5edd92891980a8b81965be1ae1694aba76350193400be59`  
Heartbeat-declared gateway goal SHA-256: `B847D638B0CA4F9C24041DCCEC2FB440861F0B27BE0441E37E288057F701B027` (does not match the on-disk goal)

## Why this freeze is needed

Iteration 212 specified a 12-episode feasibility pilot. Iterations 213–217 then changed context selection on the repeatedly used `retry-function` fixture, including a per-task TOML query. Iteration 217's 95.6580% full-lifecycle local-token reduction is valid for that paired synthetic example, but the retrieval policy was informed by repeated observations of the same task. It cannot stand in for an independent, diverse battery or establish a population success rate.

This freeze is a preregistered synthetic development pilot, not confirmatory evidence. The manifest is kept separate from the historical task and its receipts. The sealed final LoRA split is not accessed. No inference, provider call, training, or activation is authorized by this protocol.

## Frozen pilot manifest

The manifest is `examples/gateway_context_mvp/iteration218_diverse_pilot_manifest.json`. It defines 12 newly authored episodes, three independent fictional fixture repositories, and four task families per repository: source localization, bounded code repair, test/log diagnosis, and configuration/documentation. Three episodes ask for code artifacts; the localization and diagnosis episodes also require exact source evidence. Each episode fixes its input fixture files, requested output contract, evidence references, deterministic oracle, and a query template identifier before any model output is observed.

All fixture content and task text are synthetic and authored for this screen. No repository, real task, teacher trace, or sealed data is included. The set is a development pilot and must not later be relabeled as held-out or used to estimate the product acceptance population.

## Frozen context and model comparison

- Keep the existing `retry-function` task out of the 12-episode denominator.
- Compare full frozen repository context with deterministic Wrench-prepared context for each identical episode.
- Use the exact same model, decoding, output limit, verifier, bounded retry/recovery policy, and fixture snapshot in both arms.
- The initial local feasibility candidate remains Qwen3.5-4B BF16, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, without LoRA. This is not a model-size selection.
- Use the frozen task query template and the same E0 retrieval/serialization policy across episodes. Do not hand-tune query wording, evidence selection, budgets, prompts, or verifier behavior after seeing generated outputs. Any implementation change requires a new manifest version and new pilot IDs.
- Alternate arm order with a preregistered seed. Keep every failed attempt, abstention, retry and recovery fetch in the receipt and denominators.

Before execution, a separate admission record must pin the manifest and runner hashes, actual goal hash, model/runtime snapshot, output paths and peak storage. Re-read the goal and repository state; require an unambiguous goal identity; run the full storage status/reservation including every external Wrench root and the Docker WSL model volume; verify at least 5 GiB on C:; check the exact process list and output nonexistence; and sample >=10% free RAM and VRAM immediately before and throughout inference. If any gate fails, do not run the model.

## Outcomes and reporting

Count a task as locally verified only when its exact predeclared oracle passes. Report the denominator, paired outcomes and uncertainty; 12 synthetic episodes are feasibility evidence only. Report target-tokenizer input counts separately from actual input and output token IDs passed through generation. Compute full-lifecycle local-model tokenizer reduction from all attempts. Frontier calls/tokens, provider usage, billed savings, energy and all-in cost remain `null` unless directly measured under separately authorized conditions. A zero-call provider-free run is not evidence of frontier savings.

The pilot's purpose is to determine whether the frozen retrieval and verification harness is stable enough to justify a larger repository-grouped study. It cannot select the overall best model size or prove the LoRA's value, 95/5/95 acceptance, 95% lower all-in cost, or all-day engineering.

## Admission outcome for this turn

The storage checker returned `WITHIN_LIMIT` after scanning the required repository, approved data root, worktrees, external model volume, automation directory and recorded Wrench temporary source. Accounted usage was 32,709,649,011 bytes; active reservations were 36,103,000 bytes; C: had 116.48 GiB free. A 100,000,000-byte reservation was made for this bounded manifest freeze. The earlier `BLOCKED_SCAN` came from explicitly adding all of `AppData\\Local\\Temp`, which includes the inaccessible non-Wrench `WinSAT` directory; that broad operating-system temp root is not a Wrench data root. No excluded Wrench temporary path was found in the checker inventory.

This protocol does not execute the pilot. The current gateway-goal hash mismatch is unresolved, and a reusable multi-family runner plus task-specific deterministic code verifiers still need to be frozen before model inference.
