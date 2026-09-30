# Iteration 184: score admission caught and fixed fit-manifest hash shadowing

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Outcome

The first 64-row dev-score launch, `WRENCH-QWEN35-4B-DEV-SCORE-20260929-01`,
stopped at the scorer's preflight-identity gate before model loading and before
loading any dev prompt or oracle row. It produced no predictions and made zero
provider calls. Its failure receipt records
`preflight receipt does not match the current exact scorer package and inputs`.

The mismatch was a variable-shadowing bug in `load_fit_receipt()`. The function
stored the fit-manifest SHA in `digest`, then reused that name as the loop
variable for trainer/protocol hashes. The final loop value, the training
protocol SHA, was returned as `fit_sha`. The preflight therefore wrote the
protocol SHA in `training_manifest_sha256`, and score admission correctly
rejected it against the actual fit-manifest SHA. The loop variable is now
`expected_digest`, preserving the fit-manifest hash for the return value.

The score package had passed static review in Iteration 183, but that review
missed this dynamic interaction. The scorer's own exact admission check caught
it before inference. The review report remains historical and unchanged.

## Run evidence

| Artifact | SHA-256 |
|---|---|
| Iteration 183 static review | `1C023097BC770262076D1EE2B8CE891387D82CF7FF78A3B5BC9A17336D4E12EC` |
| Failed score `failure.json` | `1B53FD378CAF8EBA9C32E53204E0BD5524926A380ECFB21042C7967863870A62` |
| Failed score `resources.jsonl` | `0F7638D778FDB16E573C0FE3ABDE56D1924B851EC244F628FF51CD355A634850` |
| Corrected scorer source | `F7FCBC03D1EE4144096D5E7D3BEEE685A7E8A15B091385ABC1BCAAB74595B1FA` |

The failed job's two resource samples recorded no breach: minimum free RAM was
30.67% and minimum free VRAM was 15,214 / 16,311 MiB (93.27%). It made no model
allocation. The 1,000,000,000-byte score reservation was released after the
job stopped and its failure/resource files were accounted.

## Next gate

The corrected scorer has not yet been independently reviewed or executed. Get
a fresh exact-hash review of the patched scorer for a one-prompt preflight,
then run only a new one-shot preflight with a fresh 500,000,000-byte storage
reservation, >=5 GiB destination headroom, and live >=10% RAM/VRAM admission.
If that receipt passes, obtain a separate full-score review against the new
scorer and receipt identities before another 64-row run. Keep the held-out
split sealed. No score result, task-quality claim, Frontier usage, savings, or
all-day engineering result is established here.
