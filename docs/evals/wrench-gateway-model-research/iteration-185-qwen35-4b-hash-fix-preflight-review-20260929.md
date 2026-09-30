# Iteration 185: scorer hash-fix preflight review

Assignment: `WRENCH-QWEN35-4B-HASH-FIX-PREFLIGHT-PACKAGE-REVIEW-ITER185-20260929`  
Nonce: `9cfcac87-c0d9-47af-9dae-870d5db905fe`  
Verdict: **HOLD for a fresh one-prompt preflight**.

## Exact identities

| Item | Before and after SHA-256 / identity |
|---|---|
| Repository HEAD | `af01304824f079a64b6c3902397a2034b843511a` |
| Patched scorer | `F7FCBC03D1EE4144096D5E7D3BEEE685A7E8A15B091385ABC1BCAAB74595B1FA` |
| Schema-contract protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Gateway goal | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| Iteration 184 report | `407C5B5D28A2BB049008849C0C101B5FDB86E1D6C856CCEA6E5B0683E473A1B7` |
| Iteration 183 review | `1C023097BC770262076D1EE2B8CE891387D82CF7FF78A3B5BC9A17336D4E12EC` |

All supplied identities match. HEAD and assigned source identities were
unchanged after review.

## Blocking finding: fit-manifest hash is still shadowed

In `load_fit_receipt()`, `digest` is first set to the SHA-256 of the fit
manifest and checked against `FIT_MANIFEST_SHA`. The later resource/epoch loop
still binds `digest` as its loop variable:

```python
for path, digest, label in ((FIT_RESOURCE_LOG, FIT_RESOURCES_SHA, "fit resource log"),
                            (FIT_EPOCHS, FIT_EPOCHS_SHA, "fit epoch metrics")):
```

After the loop, `digest` is `FIT_EPOCHS_SHA`, so `return run, digest` returns
the epoch-metrics hash instead of the verified fit-manifest hash. Iteration 184
renamed the trainer/protocol loop variable, but this earlier loop still
overwrites it.

The preflight writes that returned value into `training_manifest_sha256`, so
the new receipt would label the epoch-metrics hash as the training manifest
identity. `training_protocol_sha256` is separately written from
`TRAIN_PROTOCOL_SHA` and is correct. The full-score gate calls the same
function and compares its returned value to the preflight field, so both sides
can agree on the wrong epoch hash and admit the mislabeled receipt. The actual
fit manifest is initially hash-checked, but its identity is not preserved in
the receipt binding. This is the exact admission-integrity defect under
review; repair the remaining shadowing and obtain a fresh exact-hash review
before preflight.

## Preserved preflight controls

Static inspection confirms the intended fresh preflight remains limited to
one prompt for both base and LoRA arms, with the shared fixed schema contract,
96-token output cap, cooperative 300-second generation budget, local-only
model/tokenizer loading, no provider route, and no oracle read in preflight.
The scorer retains prompt projection hashes, the synthetic dev split pin,
reparse/path and output caps, reservation/headroom checks, resource monitoring,
and 10% RAM/VRAM abort floors. Its results remain a schema/runtime diagnostic,
not product-quality, savings, or all-day engineering evidence. None of these
controls resolves the shadowed fit-manifest digest.

## Review scope and resources

Commands used: `git rev-parse HEAD`; `Get-FileHash` on the assigned scorer,
protocol, goal, and reports; bounded `Get-Content` on scorer sections and
reports; `rg` searches restricted to the scorer; `Get-CimInstance
Win32_OperatingSystem`; and `nvidia-smi` resource query. Review-time sample:
RAM free `30.68%` (`10,274,348 / 33,486,624` KiB); pinned RTX 5060 Ti
`15,236 / 16,311` MiB VRAM free. These are static-review observations, not
preflight admission.

No source or protocol was changed. No tests, Python/runtime command, model
load, inference, training, benchmark, network/provider/SubRoute call,
credential access, spending, or prompt/oracle payload read occurred. This
HOLD applies to preflight only and does not authorize a score run.
