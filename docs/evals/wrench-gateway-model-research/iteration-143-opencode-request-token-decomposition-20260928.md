# Iteration 143: decompose lowered-request tokens at the OpenCode boundary

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-OPENCODE-REQUEST-COST-DECOMP-ITER143`  
Status: **a paired two-request mock replay reproduced 42.262% input-token reduction; removing every tool schema counterfactually saves only 48.549% on this task, so schema filtering alone cannot meet 95%**  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Active gateway-goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Question

How much of one actual OpenCode read-tool cycle is attributable to tool
schemas, system messages, and the tool result, and what can tool filtering
contribute toward the 95% frontier-token goal?

## Paired request-boundary run

The run used installed OpenCode 2.0.12 with an isolated project/config/home
and a loopback-only OpenAI-compatible mock. The mock issued the same scripted
`read` call in each arm, verified the exact fixture bytes, and returned a fixed
answer. Both arms made two local requests: tool selection and tool-result
continuation. Baseline and filtered non-system messages were byte-equal;
original lowered bodies were hashed in memory, not saved. No request reached
SubRoute, OpenRouter, or any external provider.

| Arm | Tool schemas | Requests | Target-token input | Request bytes |
|---|---:|---:|---:|---:|
| Full tool inventory | 12 | 2 | 13,298 | 52,942 |
| Fixed `read` profile | 1 | 2 | 7,678 | 28,594 |
| Paired reduction | 91.667% fewer schemas | same count | **42.262% fewer tokens** | 45.985% fewer bytes |

The MiniMax M3 target-token counter used pinned tokenizer revision
`f0e1c1e04d40177e4673a22097036854f536e9c0` and inventory SHA-256
`86d0d4866b4278ce7957644e81e43ce90da356fdd434abfa8c928b4f1adfcc9c`. The
actual lowered request hashes and exact counts are in the receipt. OpenAI
JSON-string tool-call arguments were parsed to objects only in a
measurement-only copy because the tokenizer's chat template requires
structured arguments; the original body hashes were not changed. These are
local tokenizer counts, not provider usage or billing.

The earlier paired run in Iteration 101 measured 13,306 baseline tokens and
7,678 filtered tokens, a 42.2967% reduction. This repeat is within eight
baseline tokens and has the same filtered total. Each run is a single tiny
synthetic task. This close repeat supports reproducibility for that fixture,
not for a representative engineering workload.

## Counterfactual component ablations

The runner tokenized separate request variants from the exact captured
messages. These ablations were **never sent** and are not valid requests. Each
one removes a different component, so their reductions are not additive.

| Arm | Exact input | Without any tool schemas | Without system messages | Without tool-result messages |
|---|---:|---:|---:|---:|
| Full inventory | 13,298 | 6,842 (**48.5487% fewer**) | 6,956 (**47.6914% fewer**) | 13,243 (55 fewer) |
| `read` profile | 7,678 | 6,846 (**10.8362% fewer**) | 1,332 (**82.6517% fewer**) | 7,623 (55 fewer) |

Removing all tool schemas while retaining the exact baseline messages saves
only 48.55% on this paired cycle. The reduction from the actual full
inventory to one `read` schema is 42.262%. The unchanged system-message
content is a comparably large part of this request; the read result itself
accounts for only 55 tokens in this synthetic fixture. This establishes a
task-specific ceiling for schema filtering, not a general ceiling for every
OpenCode task. It also shows why removing instructions or tool results merely
to increase a percentage would not be a valid product improvement.

For the requested **full-lifecycle frontier-token** metric, the main path to
95% must therefore be local verified completion that avoids frontier requests
for most episodes. Schema filtering and context compaction can add savings on
the remaining routed episodes, but neither should be presented as the primary
95% proof by itself. Unequal episode lengths, retries, verification,
compaction, recovery fetches and cache behavior still require a frozen paired
workload ledger.

## Verification, failed attempt, and identities

The successful receipt reports status `complete`, four loopback mock requests,
two verified mock tool cycles, zero provider calls and zero billed cost. A
mock-scripted result is not model reasoning or coding-task success.

| Item | Bytes | SHA-256 |
|---|---:|---|
| Successful paired receipt `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\opencode-read-task-cost-components-iter143.json` | 6,319 | `3572B771BE5757B49C40C2F9C9FD2E581A430BB5D637DB0A4F553012A7F83471` |
| Failed initial receipt `C:\wrench-slm-data\artifacts\wrench-gateway-demo-mvp\opencode-read-task-cost-decomp-iter143.json` | 199 | `AC2D1211296486078A561F389D0C0118350D2B53DDC986AED154E81426B9F404` |
| Cost-decomposition harness `examples/opencode_v2_subroute_tool_profiles/no_provider_read_task_cost_decomposition_017.mjs` | — | `EB8CC2F0F94DA9148213EA075C42627CA2FA673F6E58E4EA9969196F2D1D3638` |
| Installed `tool_profiles.mjs` | — | `19769A4229878C9AC0C42CE93B3F44CDE8864A7121D6FCA94363F3E92EF8B014` |

The first invocation mistakenly used the older 014 runner and failed closed
with `read_only_profile_not_a_strict_tool_subset` before the filtered arm.
Its 199-byte receipt hash is identical to the already documented Iteration
101 attempt 014, so it is retained as the same failure observation, not counted
as a new pass. The completed replay used a copy of the previously successful
016 runner with a unique job directory and receipt path.

`node --check` passed on the new harness; `git diff --check` passed with the
repository's existing line-ending warnings. Resource samples were discrete,
not continuous: RAM free was 19.27% before, 18.96% and 16.88% during, and
19.30% after; VRAM free stayed above 93.3%. All observed samples remained
above the 10% run floor. A pre-existing `opencode.exe serve --service`
process was observed with a 10:13 AM creation time and left untouched; the
runner's own Node process completed with exit code 0.

Storage admission reserved `100,000,000` bytes under this assignment and
included the approved Wrench root, automation directory, and Docker WSL model
volume. C: had 139,266,973,696 bytes free at the final check. The aggregate
storage scan remained below the 50 GB limit. No model was loaded, trained, or
downloaded, no credentials were read, and no SubRoute or provider configuration
was changed.

## Next action and limits

Use a frozen, answer-blind local-completion battery to measure the share of
mechanical and context tasks that deterministic Wrench plus the candidate SLM
can complete without any frontier request. Keep complete request accounting
for the tasks that do route. The answer-blind local 0.8B matrix has only three
synthetic lookup cases; a same-task 0.8B-versus-2B comparison and a trained
Wrench LoRA result are still missing. The 95% local-completion, 5% routing,
95% success-retention, 95% frontier-token and all-in-cost savings, and all-day
engineering gates remain unproven.
