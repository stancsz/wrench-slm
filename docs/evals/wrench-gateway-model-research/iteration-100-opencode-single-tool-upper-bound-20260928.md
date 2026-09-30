# Iteration 100: OpenCode single-tool token upper-bound slice

Date: 2026-09-28 (America/Edmonton)  
Assignment: `WRENCH-OPENCODE-MOCK-RUNTIME-013-20260928`  
Status: **installed-runtime request shaping passed; 42.5735% target-token reduction on one synthetic read-only request; task utility remains unknown**  
Wrench HEAD: `af01304824f079a64b6c3902397a2034b843511a` (working tree dirty)  
Gateway goal SHA-256: `D6EE8ABF38EF643C58D0FE513361831BE9341E32E4794128BBF0BF7E178E2E95`

## Result

This is a second paired synthetic preflight on installed OpenCode `2.0.12`,
using the same harness mechanics as Iteration 099 but an allowlist that retains
only `read`.

| Arm | Tool schemas | Exact request bytes | MiniMax M3 target-token input |
|---|---:|---:|---:|
| Baseline | 12 | 26,241 | 6,598 |
| Single-tool profile (`read`) | 1 | 14,067 | 3,789 |
| Reduction | 91.6667% fewer tools | 46.3930% fewer bytes | **42.5735% fewer tokens** |

The paired user and non-system messages match exactly. System messages differ
between tool profiles and are included in the exact target-token counts. The
fixed profile removes 11 schemas; it does not ask a learned selector to choose
the profile. OpenCode's local mock always returned `MOCK_OK`, without calling
the remaining `read` tool. Therefore this is a token-overhead upper-bound slice
for a synthetic request that explicitly needs no tools. It supplies no
evidence that read-only access is sufficient for repository engineering, nor
that the more aggressive profile retains task success.

The immediately prior three-tool result in Iteration 099 retained `read`,
`grep`, and `glob`, and measured 35.8539% on its own paired baseline. The
single-tool slice measured 6.7196 percentage points more token reduction. Its
own baseline is 6,598 tokens versus 6,599 in Iteration 099 because each run
uses a different isolated job path; compare each reduction only within its own
pair.

## Measurement identity and limits

The exact request-body hashes are:

- Baseline: `6f66cb1947c199740d6bc0eb1380d8cf9ca7d4fc73748ec87d9e42f68c63eef9`
- Single-tool: `3c84df21a007bd6bf8c3709e6a71afa0e75c9a9d77cb592a57acb379b63ab770`

Receipt: `C:\\wrench-slm-data\\artifacts\\wrench-gateway-demo-mvp\\opencode-request-preflight-013.json`  
Size: 2,888 bytes  
SHA-256: `84e7eab108cfbdb82409d0d0ad523d60daab2c32975d97f05dccf7891d6247ec`

It binds the OpenCode v2.0.12 binary SHA-256
`58d550b26e9241759a6906c65f1e0605eaf512d63cbaf6d8eb472375b9311c95`,
tool-profile source SHA-256
`19769a4229878c9ac0c42ce93b3f44cde8864a7121d6fca94363f3e92ef8b014`,
current harness SHA-256
`c0dbd70e77d203007dd474a5e556167249e3f4c61a53d4f7f462e0bfbf087b0f`, and
the same pinned MiniMax M3 tokenizer revision and inventory as Iteration 099.
The tokenizer reads validated `input_ids` from a `Mapping`; no provider usage
was returned or billed.

The isolated loopback mock received two requests. SubRoute
`127.0.0.1:4000` and the forced OpenRouter provider were not contacted or
changed. No credential was read. Child environments were scrubbed, OpenCode
was isolated, npm resolution was offline, and the receiver accepted loopback
peers only; no OS-wide firewall change was made. System RAM and GPU memory
had pre-run samples of 27.48% and 15,204 MiB free respectively. A continuous
minimum was not captured, so sustained resource-floor compliance remains
unverified. The unique storage reservation was 100,000,000 bytes; aggregate
storage remained below 50 GB.

## Decision and next experiment

This confirms the mechanical token savings rise as tool availability narrows
on this one synthetic prompt. It does not identify the best production
profile. Select the profile on a frozen coding workload, then compare it
against all 12 tools for verified task completion, required-action coverage,
tool-call success, retries, abstentions, human rescue, and recovery. Report the
highest token reduction that satisfies the preregistered quality bound, rather
than selecting the maximum from this no-tool task.

The measurement does not establish 95% frontier-token savings, 95/5 routing,
95% retained task success, lower all-in dollars, LoRA value, or sustained
engineering. Paid provider comparison still requires an enforced aggregate
spend cap and durable usage receipt.
