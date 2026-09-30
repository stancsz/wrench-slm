# Iteration 195: Qwen3.5-4B full-score package review

Assignment: `WRENCH-QWEN35-4B-FULL-SCORE-REVIEW-ITER195-20260929`  
Nonce: `7ef82212-dcd9-48a8-bd55-2142527cfdbc`  
Verdict: **PASS for the bounded 64-row synthetic development score package, subject to fresh score-job admission.** Static review only; this report does not start or authorize a run by itself.

## Exact identities

| Item | SHA-256 / identity |
|---|---|
| Repository HEAD before review | `af01304824f079a64b6c3902397a2034b843511a` |
| Repository HEAD after review | `af01304824f079a64b6c3902397a2034b843511a` |
| Scorer before and after | `4E2E69E1AE89B553470FE3ABE9EE5776C70D35942B99E8B4509C7FA71F159E85` |
| Evaluation protocol before and after | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Gateway goal | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| Iteration 194 preflight report | `B9B13E5545335884EA73C56E018AA5E137EBA06E8AB1CEF833ED06C5852E3984` |
| Iteration 193 preflight review | `67E88567942969DA87784DA2BA7798FDE804D18F135BEFD8320B85D4DACE6475` |
| Iteration 191 prior score HOLD | `49A17FD073F0BAC721BE050C5A6DA0A0F6F54B5B764D5E4008ABAFBF97C5B6D2` |
| Preflight 10 receipt | `2EE25973921278FFE5491A5DD105F95A8F0219EC84943FFBEB577E268B1909C1` |
| Preflight 10 base predictions | `462C2BD0B6900C8D76983C581930C64947F3B5AF27C3A39B48424A47C7A69720` |
| Preflight 10 LoRA predictions | `F4A04A9A56F62FCBFB84B03342AA624CCCA4149D0579674D380CEE964CFCE9E9` |
| Preflight 10 resource log | `D54809BC08600F5FAD93CFA3D5D2820AFA39EDD9366437E2C7ADBFADCE8F4D75` |

## Findings

Preflight 10 reports `PREFLIGHT_COMPLETED`, mode `preflight`, one prompt, the expected repo HEAD, current scorer and evaluation-protocol hashes, fit manifest SHA `d39a9335fbdd107390f053f2460a34845ce3efe2ea473f73060c6eae85278f0e`, and separate training-protocol SHA `4b123714bb3c669a98b4d892bd127d69a10adcdb6763cc4059b66fae128e9893`. Its prompt manifest SHA `dc4c3b605f7cc2ac62aa283bdd90b55fbcda7cb4bf526441306ec25508167939` is distinct from the prompt payload SHA `6be3c1e65342711af8fcb7c6f44ed53b5986d31ad93fe0c9ee1542e537268baf`. These values match the current source constants and the score-mode comparisons. The receipt also matches scorer/protocol, model ID/revision/config/inventory, dataset/dev, adapter, runtime/Python, GPU, chat-template, reservation, and zero-frontier-call bindings. The exact receipt, two prediction-file, and resource-log hashes match the supplied identities. The two predictions report the same prompt ID. The preflight reservation file is absent, so its reservation has been released; the score gate validates its embedded reservation record and allows this absent active-record state.

Static inspection of score mode confirms it reads the pinned prompt-only projection and requires 64 unique rows. The model sees only the transformed system/user messages; no combined labeled source or held-out path is read. Both arms' raw prediction files are written, flushed, and hashed before `load_oracle_projection()` is called. The oracle projection is separately hash-pinned and checked for 64 unique rows after prediction sealing. No provider client or route is present. Runtime bootstrap enforces offline mode; tokenizer/base load with `local_files_only=True` and `trust_remote_code=False`; the adapter is read-only and inactive.

The validator enforces exact output keys, closed route/operation/reason enums, boolean and list types, unique evidence IDs drawn from visible request records, and rejects authority-like extra keys via the exact-key check. Output files cap at 20 MiB each and aggregate outputs at 128 MiB; full-score scratch caps at 512 MiB. Output, log, and scratch paths are checked under the approved root with symlink/junction/reparse checks and checks repeated around writes. These are cooperative path guards with a documented time-of-check/time-of-use race limitation. The score run monitors RAM/VRAM and requires at least 10% free throughout. Generation `max_time=300s` is cooperative; the protocol requires external supervision with a 14,400-second overall hard timeout and recording forced termination as failure. The score job must use a fresh unique reservation of at least 1,000,000,000 bytes, include every external Wrench root, remain under the aggregate 50 GB ceiling, and preserve at least 5 GiB destination headroom. No such score reservation or live score-resource admission was checked or granted by this review.

This synthetic dev diagnostic cannot establish coding effectiveness, Frontier usage or savings, all-in cost, or reliable all-day engineering. Local tokenizer counts are not provider tokens. Held-out data stays closed. This is a static package PASS, not execution authority.

## Review-time resources and scope

RAM free at review: `30.67%` (`10,270,048 / 33,486,624` KiB). RTX 5060 Ti: `15,196 / 16,311` MiB VRAM free. This sample is not score-job admission; recheck immediately before the score job and monitor throughout.

Commands used: `git rev-parse HEAD`; `Get-FileHash` on assigned scorer, evaluation protocol, gateway goal, Iterations 191/193/194 reports, preflight receipt, prediction files, and resource log; bounded `Get-Content` on scorer sections, protocol, Iteration 194 report, and preflight metadata; `rg` searches restricted to the scorer; `Get-ChildItem` to locate the exact preflight directory; `Test-Path` on the preflight reservation record; `Get-CimInstance Win32_OperatingSystem`; and `nvidia-smi --query-gpu=uuid,name,memory.total,memory.free --format=csv,noheader,nounits`.

No prompt or oracle payload was opened. Prediction payloads were not opened; only their supplied paths and hashes were checked. No tests, Python/runtime command, model load, inference, benchmark, network/provider/SubRoute call, credential access, spending, or source mutation occurred. Only this review report was created.
