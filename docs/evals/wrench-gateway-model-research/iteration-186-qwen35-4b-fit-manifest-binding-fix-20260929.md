# Iteration 186: preserve the exact fit-manifest hash through score receipts

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Findings and repair

The 64-row launch `WRENCH-QWEN35-4B-DEV-SCORE-20260929-01` failed before
model loading. Iteration 184's first source repair renamed the trainer/protocol
loop variable, but the Iteration 185 exact-hash review found that an earlier
resource/epoch-metrics loop also reused `digest`. With only the first loop
fixed, `load_fit_receipt()` still returned `FIT_EPOCHS_SHA` instead of the
verified fit-manifest SHA. The preflight receipt from attempt 08 had recorded
the protocol SHA; after the first partial repair, score mode expected the epoch
metrics SHA. This explains the fail-closed identity rejection in attempt 01.

The corrected source now uses `manifest_digest` exclusively for the fit
manifest and `expected_digest` for both later verification loops. Thus the
return value and `training_manifest_sha256` stay tied to `FIT_MANIFEST_SHA`,
while `training_protocol_sha256` remains independently tied to
`TRAIN_PROTOCOL_SHA`. The source change is not yet independently reviewed or
executed.

## Exact identities and no-run boundary

| Item | SHA-256 / identity |
|---|---|
| Repository HEAD | `af01304824f079a64b6c3902397a2034b843511a` |
| Corrected scorer source | `A64F4D7A92EFC7CAE3EECBA7BB21A62A566C06867D31EB991CCE4F0BB19A877D` |
| Evaluation protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Iteration 185 HOLD review | `934D9EE172F775C96B13116ADFBF0ACC8AB956A0ACA928B767BE3FEA49A50E17` |
| Failed score receipt | `1B53FD378CAF8EBA9C32E53204E0BD5524926A380ECFB21042C7967863870A62` |
| Failed score resource log | `0F7638D778FDB16E573C0FE3ABDE56D1924B851EC244F628FF51CD355A634850` |

No new preflight, score, tests, model load, inference, or prompt/oracle read was
performed after the source edit. The only source change was the fit-manifest
hash variable repair; `git diff --check` found no whitespace errors (only
existing line-ending notices). Iteration 185's HOLD remains in effect for the
unreviewed code identity.

## Next gate

Obtain a new exact-hash static review of this corrected scorer for a one-prompt
preflight. On PASS, use a new preflight job ID, fresh storage status and
500,000,000-byte reservation, >=5 GiB destination headroom, and live >=10% RAM
and VRAM admission. Review the resulting receipt and scorer hash again before
reserving or running a new 64-row score. The prior score attempt is one-shot
and must not be reused. No current evidence establishes model utility,
Frontier-token savings, cost reduction, or all-day engineering reliability.
