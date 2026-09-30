# Iteration 191: Qwen3.5-4B full-score receipt and protocol review

Assignment: `WRENCH-QWEN35-4B-SCORE-RECEIPT-PROTOCOL-BINDING-REVIEW-ITER191-20260929`  
Nonce: `56aeac10-ae72-4660-905b-e8b8eb95ef27`  
Verdict: **HOLD for full scoring**. This is a static review and grants no
execution authority.

## Exact identities

| Item | SHA-256 / identity |
|---|---|
| Repository HEAD, before and after | `af01304824f079a64b6c3902397a2034b843511a` |
| Current scorer | `ACB5AB2D497531E6676CCAA8779BBAE1B39E3D99D5DA57189699F435B28B8EDA` |
| Evaluation protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Gateway goal | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| Iteration 190 report | `A230C81DFAEB6ED28F0A97B87D32325165328A88306BAB4B3B77690F627BE00D` |
| Iteration 188 report | `F7BA9D4DEB6F2AE797F12FB5AD4EF7DDB16DB8B5D00378B890721E702DA5ACCC` |
| Iteration 187 preflight review | `B97844DABEB239A43D8EDB6D769E6951C691AEE450DE2E5F011DD8DCC894C74F` |
| Iteration 183 historic score review | `1C023097BC770262076D1EE2B8CE891387D82CF7FF78A3B5BC9A17336D4E12EC` |
| Preflight 09 receipt | `5F2F875404B8531BDA0B9A09C02332DC213E69A4814C9DE1A23426CA3476E9DD` |
| Preflight base predictions | `B60AE4B7FB9595DF15E93D28F02B78BB25C74E5B97896743BA286FD1400F0733` |
| Preflight LoRA predictions | `C7C9F13891A24D118999B23984B738AA968C4CD2AEA2C74CAB25558DB50363B5` |
| Preflight resource log | `B92DDD78CC1DCF90640F38F04853A9A655B46676D3166F61AADDB39C5945BAC9` |

All supplied hashes match. The preflight metadata reports `PREFLIGHT_COMPLETED`,
the expected HEAD, scorer SHA `A64F4D7A92EFC7CAE3EECBA7BB21A62A566C06867D31EB991CCE4F0BB19A877D`, and the expected protocol SHA. It records the exact fit manifest
`D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E`
separately from training protocol
`4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893`.

## Blocking receipt-binding findings

1. **Preflight 09 is stale for the current scorer.** Its receipt binds evaluator
   SHA `A64F4D7A...`, while the current scorer is `ACB5AB2D...`. Score mode
   compares the receipt's `evaluator_sha256` to the current scorer hash and
   will reject this receipt. A fresh preflight must use the current scorer
   identity after source repair.
2. **The current scorer mislabels the prompt manifest hash.** The pinned
   constants distinguish prompt payload SHA `6be3c1e6...` from prompt-manifest
   SHA `dc4c3b60...`. `load_prompt_projection()` verifies the manifest file,
   but returns `PROMPT_PROJECTION_SHA`. Preflight assigns that return value to
   `prompt_manifest_sha256`, producing the payload hash in that field. Score
   admission compares the field with `PROMPT_MANIFEST_SHA`, so a fresh
   preflight made by the current scorer would fail the prompt-manifest identity
   check. Fix the return/binding and review a new scorer hash before creating
   another preflight.

## Controls confirmed in source

The fit-manifest binding is now correct: `load_fit_receipt()` preserves and
returns `manifest_digest` after verifying it against the fit-manifest pin.
Preflight writes that value to `training_manifest_sha256` and writes the
separate pinned `TRAIN_PROTOCOL_SHA` to `training_protocol_sha256`. Full-score
admission directly compares both fields, binds the current evaluator and
protocol hashes, and checks the receipt's model, adapter, data, runtime, GPU,
reservation, prediction, and resource identities.

Static inspection also confirms that score mode uses exactly the 64 unique
rows from the pinned prompt-only projection, seals and hashes both prediction
files before opening the separate oracle-only projection, and does not access
held-out data. The model/tokenizer load from local files with offline flags
and `trust_remote_code=False`; no provider client or route is present. The
validator enforces exact keys, closed enums, boolean and list types, unique
visible evidence IDs, and rejects extra authority-like keys through the exact
key-set check. Output/scratch caps and root/reparse checks remain in place.
Resource monitors enforce >=10% RAM and VRAM and the documented hard overall
job timeout remains externally supervised; Transformers `max_time` is
cooperative.

The score path requires a separate fresh reservation of at least
1,000,000,000 bytes and 5 GiB destination headroom. The Iteration 191 review
reservation is 50,000,000 bytes and does not admit scoring. The source accepts
an absent preflight reservation record or a still-active matching record; the
Iteration 188 report requested release after output accounting, but release
was not independently verified in this static review. Obtain fresh aggregate
storage status and account for any active reservation before score admission.

## Resources and scope

Review-time sample: RAM free `30.08%` (`10,073,296 / 33,486,624` KiB); pinned
RTX 5060 Ti VRAM `15,210 / 16,311` MiB free. This is not score-job admission.

Commands used: `git rev-parse HEAD`; `Get-FileHash` on assigned source,
protocol, goal, reports, preflight receipt, predictions, and resource log;
bounded `Get-Content` on scorer/protocol/reports and selected preflight receipt
metadata; `rg` searches restricted to the scorer; `Get-CimInstance
Win32_OperatingSystem`; and `nvidia-smi` resource query. No prompt or oracle
payload was opened. No tests, Python/runtime command, model load, inference,
benchmark, network/provider/SubRoute call, credential access, spending, or
source mutation occurred.

Only this review report was created. Full score remains blocked pending repair
of the prompt-manifest return binding, a fresh exact-hash review, a new
successful preflight bound to the repaired scorer, and separate score-job
storage/resource admission.
