# Iteration 190: compare the training protocol receipt field directly

Date: 2026-09-29  
Repository HEAD: `af01304824f079a64b6c3902397a2034b843511a`  
Gateway goal SHA-256: `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59`

## Change

Iteration 187 noted that score admission verified the fit manifest and pinned
training protocol file, but did not directly compare the preflight receipt's
`training_protocol_sha256` field. The scorer now rejects a preflight receipt
unless that field equals `TRAIN_PROTOCOL_SHA`. This complements the corrected
Iteration 186 manifest-digest handling: `training_manifest_sha256` is checked
against the actual fit-manifest SHA, and `training_protocol_sha256` is checked
against the independently pinned training protocol SHA.

## Exact identities

| Item | SHA-256 / identity |
|---|---|
| Repository HEAD | `af01304824f079a64b6c3902397a2034b843511a` |
| Updated scorer source | `ACB5AB2D497531E6676CCAA8779BBAE1B39E3D99D5DA57189699F435B28B8EDA` |
| Evaluation protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Gateway goal | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| Iteration 187 preflight review | `B97844DABEB239A43D8EDB6D769E6951C691AEE450DE2E5F011DD8DCC894C74F` |
| Iteration 188 preflight 09 report | `F7BA9D4DEB6F2AE797F12FB5AD4EF7DDB16DB8B5D00378B890721E702DA5ACCC` |

The updated scorer has not been independently reviewed or executed. Its hash
change invalidates the prior preflight receipt for exact-package admission.
No tests, inference, score, provider request, or held-out access was performed
after this edit. `git diff --check` reported no whitespace errors; it emitted
the existing repository line-ending notices.

## Next gate

Obtain a fresh exact-hash review of the updated scorer for a one-prompt
preflight. If it passes, run a new preflight under fresh storage and runtime
admission, then obtain another exact-hash review for 64-row score mode using
the resulting scorer and receipt identities. The held-out split stays sealed.
