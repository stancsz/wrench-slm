# Iteration 101: OpenCode read-tool cycle and paired schema cost

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-OPENCODE-READ-TASK-016-20260928`  
Status: **one paired synthetic read cycle completed; 42.2967% fewer target-token input tokens across both requests; no model reasoning or provider usage measured**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway goal SHA-256: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Result

Both arms ran on installed OpenCode 2.0.12 against the same isolated synthetic
project and prompt. The loopback mock returned one fixed `read` tool call,
verified that the tool result contained the complete fixture source, and then
returned a fixed final answer. OpenCode made two requests per arm: the initial
tool-selection request and the tool-result continuation.

| Arm | Tools exposed to the mock | Requests | Target-token input, both requests | Request bytes |
|---|---:|---:|---:|---:|
| Full inventory baseline | 12 | 2 | 13,306 | 52,876 |
| Fixed `read` profile | 1 | 2 | 7,678 | 28,528 |
| Paired reduction | 91.6667% fewer schemas | same count | **42.2967% fewer tokens** | 46.0474% fewer bytes |

The ratio is `(13,306 - 7,678) / 13,306`. Per-request MiniMax M3 tokenizer
counts were 6,608 and 6,698 for baseline, and 3,794 and 3,884 for filtered.
Both arms called `read`; both tool results matched the exact fixture content
and had SHA-256 `2a5275dd8a41682e2002b9956b2a1236a6a14c8a2469582e08ebc31a40545bb3`.
The fixture source SHA-256 is
`47768d6f8f561792481e8dfe58b40aba7927aeff5fc109541de07f52adb9e332`.

This is a single synthetic episode with a scripted mock, not a model-produced
success. It shows that the installed context hook changed the tool map at the
lowered OpenAI-compatible request boundary and that a retained `read` tool can
complete this one prescribed round trip. The reduction is a local target
tokenizer proxy for request shaping, not frontier tokens avoided, task-success
retention, or an end-to-end gateway result. The system prompts differ between
profiles and are included in these counts. The measurement-only tokenizer
parses OpenAI JSON-string tool-call arguments into objects because the pinned
MiniMax M3 chat template requires structured arguments; raw lowered request
body hashes remain unchanged.

## Identity and controls

- OpenCode binary SHA-256: `58d550b26e9241759a6906c65f1e0605eaf512d63cbaf6d8eb472375b9311c95`.
- Tool-profile source SHA-256: `19769a4229878c9ac0c42ce93b3f44cde8864a7121d6fca94363f3e92ef8b014`.
- Iteration 016 harness SHA-256: `9d056617b11eb6cf7f5745f8c27ac0f0e5ef7745a8e6c2f0315ba6ffe24ea255`.
- Pinned tokenizer: `MiniMaxAI/MiniMax-M3@f0e1c1e04d40177e4673a22097036854f536e9c0`; inventory SHA-256 `86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`.
- Raw lowered-request body hashes, baseline: `7804783267c47b2178ac2c97d85236ad30eb37b25054548880d2f0f8c80a0e44`, `42dfe0c53027ffa1ccb9561201a221fc844be2ecba62c12b9bf81f8faf17a7d3`.
- Raw lowered-request body hashes, filtered: `843d63f65d7d9fc7bf279c100cfe64964d58d7e38016bcfedf5523feb1ac9f37`, `791f745a97ac5c7d448f73a96398a7b9e2de943f43816cbcae8ac82f71a54af1`.
- Receipt: `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\opencode-read-task-016.json`, 4,807 bytes, SHA-256 `014d2971931126d20f180445cc5801ea936a8c8d0f871b08383f7234fd3e3d5d`.
- No SubRoute `:4000`, OpenRouter, external provider, or credential was contacted. Provider calls and billed cost are both zero. The mock was loopback-only; its request payloads were held in memory and the receipt records hashes and counts, not request content.
- Pre-run sample: 27.50% system RAM free and 15,223 MiB GPU memory free. During/after-run sample: 25.39% RAM free and 15,230 MiB GPU memory free. These samples stayed above the 10% floor; continuous resource telemetry was not captured.
- Storage admission reserved 100,000,000 bytes under job 016. Aggregate Wrench storage remained below 50 GB; C: had 143,815,811,072 bytes free at the pre-run check.

## Failed closed attempts retained

Two earlier unique attempts were not discarded or counted as passes:

1. Job `WRENCH-OPENCODE-READ-TASK-014-20260928` failed with
   `read_only_profile_not_a_strict_tool_subset`. Its receipt has SHA-256
   `ac2d1211296486078a561f389d0c0118350d2b53ddc986aed154e81426b9f404`.
   The harness configured deny permissions that removed tools from OpenCode's
   source inventory before the profile hook ran. The receipt lacks detailed
   inventory diagnostics, so this cause is an inference supported by the
   corrected 016 run, not a directly captured 014 trace.
2. Job `WRENCH-OPENCODE-READ-TASK-015-20260928` completed both tool cycles but
   failed tokenization because the M3 template expects structured tool-call
   arguments, while OpenAI-compatible messages carry JSON strings. Its receipt
   has SHA-256 `a8478a13955a73a8cebdb45ec6779eb1e4c0f79df5d2493bf660d1fcf884718c`.

Their reservations were released after each job stopped and its receipt was
counted. Job 016 has its own receipt, unique output path, and reservation.

## Claims still unproven

This result does not establish LoRA value or quality, quality-preserving
profile selection, the highest safe tool reduction on real tasks, actual
frontier-token savings, 95/5 routing, 95% retained success, 95% all-in cost
reduction, confidence bounds, or all-day engineering. It also does not prove
that exposing the full tool set is acceptable in a production route. A
production comparison still needs frozen representative coding episodes,
verified outcomes, an enforced numeric spend cap and provider usage receipts.
