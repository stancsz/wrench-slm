# Iteration 187: fit-manifest binding preflight review

Assignment: `WRENCH-QWEN35-4B-FIT-MANIFEST-BINDING-REVIEW-ITER187-20260929`  
Nonce: `782e622f-9c19-414a-84dd-1f936341cf6d`  
Verdict: **PASS for a fresh one-prompt preflight only.** This report grants no
execution authority and does not authorize full scoring.

## Verified identities

| Item | SHA-256 / identity before and after review |
|---|---|
| Repository HEAD | `af01304824f079a64b6c3902397a2034b843511a` |
| Corrected scorer | `A64F4D7A92EFC7CAE3EECBA7BB21A62A566C06867D31EB991CCE4F0BB19A877D` |
| Schema-contract protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Gateway goal | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| Iteration 186 repair report | `39C42EE89352C88511BFED21B62B02E5D1A5C0470730C9C25840D34478BA9FC3` |
| Iteration 185 HOLD report | `934D9EE172F775C96B13116ADFBF0ACC8AB956A0ACA928B767BE3FEA49A50E17` |

## Finding

The Iteration 186 repair is present. `load_fit_receipt()` stores the verified
manifest hash in `manifest_digest`, compares it with `FIT_MANIFEST_SHA`, and
uses `expected_digest` as the loop variable for both the resource/epoch loop
and trainer/protocol loop. It returns `run, manifest_digest`; neither loop can
overwrite the manifest identity.

Preflight writes `training_manifest_sha256` from the returned `fit_sha`, so it
records `FIT_MANIFEST_SHA`. It writes `training_protocol_sha256` separately
from `TRAIN_PROTOCOL_SHA`; these are distinct values and correspond to the
fit-manifest and training-protocol inputs respectively. In `score-dev`, the
preflight manifest field is compared with the corrected `fit_sha`. The score
path also independently rechecks the fit manifest's embedded training
protocol SHA against `TRAIN_PROTOCOL_SHA` and verifies the pinned protocol
file. The corrected receipt can therefore satisfy the intended identity
binding. It also records the current scorer hash as `evaluator_sha256`, and
score admission requires that value to match the current scorer hash.

One hardening caveat: score admission does not directly compare the receipt's
`training_protocol_sha256` field. The training protocol remains independently
verified through the fit manifest and pinned protocol file, so this omission
does not block the fresh preflight reviewed here. Keep the full-score gate
under its own exact-hash review before any score launch.

## Preserved preflight controls

Static review confirms preflight reads at most one row from the pinned
prompt-only projection, runs both base and inactive LoRA arms on the same
schema-contract-augmented messages, and does not open the oracle projection.
The model and tokenizer use local files only, offline flags, and
`trust_remote_code=False`; the scorer has no provider client or routing call.
The run records evaluator, fit manifest, training protocol, model/config,
inventory, dataset/dev, adapter, runtime/Python, GPU, prompt projection,
reservation, prediction, and resource identities. Output and scratch limits,
path checks, reservation/headroom checks, and the live 10% RAM/VRAM resource
floors remain in place. The one-row result is only a schema/runtime gate and
supports no model-quality, token-saving, cost, or sustained-engineering claim.

## Resources and review scope

Review-time sample: RAM free `30.81%` (`10,315,740 / 33,486,624` KiB); pinned
RTX 5060 Ti VRAM `15,223 / 16,311` MiB free. This is not a preflight runtime
admission; obtain fresh storage status, a unique 500,000,000-byte preflight
reservation, 5 GiB destination headroom, and live 10% RAM/VRAM admission before
any run.

Commands used: `git rev-parse HEAD`; `Get-FileHash` on the assigned scorer,
protocol, goal, and reports; bounded `Get-Content` on scorer sections and the
Iteration 186 repair report; `rg` searches restricted to the scorer;
`Get-CimInstance Win32_OperatingSystem`; and `nvidia-smi` resource query. No
source or protocol was changed. No tests, Python/runtime command, model load,
inference, training, benchmark, network/provider/SubRoute call, credential
access, spending, or prompt/oracle payload read occurred.
