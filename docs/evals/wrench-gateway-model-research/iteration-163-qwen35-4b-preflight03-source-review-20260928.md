# Iteration 163: Qwen3.5-4B attempt-03 source review

- Assignment: `WRENCH-QWEN35-4B-PREFLIGHT03-REVIEW-ITER163-20260928`
- Nonce: `f3f57d82-d55e-43dc-bde7-e2c476b655fe`
- Verdict: **CONDITIONAL for the one-step preflight only. No fit authorization.**
- HEAD before/after: `af01304824f079a64b6c3902397a2034b843511a`
- Gateway goal hash: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

| Identity | SHA-256 before and after |
|---|---|
| Trainer | `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5` |
| Protocol | `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893` |
| Attempt 01 report | `43D908F90F4DBB50679CDB7F80E31918E34B4B7BEBFABE6525021DE456E40F0B` |
| Attempt 02 report | `7C14F73B684302DB6DD50AC6EB114D03EAB5A98075367764313460529B71D413` |
| Chat-template boundary diagnostic | `AE1584CCC6C06AD4E6F47E53627B4E29A1694597AEBA9F508D90EE17E5B5B7EF` |
| Iteration 162 rejection report | `2024F6B4E7ADB26AF002B84011D1ADFBC798490A3778B2F153BA4A2FFB1DE21A` |
| Pinned-tree helper | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| Pinned config | `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670` |

The reviewer confirms attempt 03 closes the specific Iteration 162 rejection: offset starts and ends are both range-checked and nondecreasing. The source requires the fast tokenizer, uses one full serialized conversation tokenization with offsets, masks all tokens starting before the prompt boundary, rejects non-whitespace tokens crossing that boundary, and rejects absent answers or empty targets. Attempt 03 has distinct job, log, and job-scoped cache paths. Protocol resource/storage, offline, synthetic-only, and held-out controls remain in place.

The review is limited to allowing a bounded one-step preflight after a fresh exact storage reservation, destination headroom check, and live >=10% RAM/VRAM sample. It does not authorize a 96-step fit or support model quality, production utility, token savings, 95/5 routing, cost savings, or all-day engineering claims.

Reviewer resources: RAM available 8,549 MiB at start and 8,517 MiB at end; RTX 5060 Ti VRAM free 15,190/16,311 MiB and 15,206/16,311 MiB.

Commands were limited to `git rev-parse HEAD`, visible before/after `Get-FileHash`, bounded `Get-Content`/`rg` on assigned files, and RAM/VRAM samples. No tests, Python/AST, tokenizer/model/runtime load, preflight, inference, training, benchmark, provider/network/SubRoute call, spending, held-out access, or file edits occurred. No reviewer report artifact was created.

## Remaining gates

Before attempt 03, reserve at least 250,000,000 bytes under `WRENCH-GATEWAY-LORA-SCREEN-03-QWEN35-4B-PREFLIGHT-20260928-03`, include every external Wrench path, confirm at least 5 GiB additional destination headroom, and take fresh >=10% RAM/VRAM samples. A later fit remains gated on successful matching preflight, a separate 2 GB reservation, >=25% free RAM at fit start, and >=10% free RAM/VRAM throughout.
