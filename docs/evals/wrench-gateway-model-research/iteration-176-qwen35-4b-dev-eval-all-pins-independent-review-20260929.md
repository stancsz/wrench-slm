# Iteration 176: independent exact-hash review of Qwen3.5-4B dev pins

Assignment: `WRENCH-QWEN35-4B-DEV-EVAL-REVIEW-ITER176-20260929`  
Nonce: `1d6125d5-6e38-4927-bbd3-53dbe41329ce`  
Expected HEAD: `af01304824f079a64b6c3902397a2034b843511a`

## Verdict

**PASS for the static pin review.** The current trainer and prompt-helper
literals match the current files; the pinned fit manifest's `runner_sha256`
matches the trainer; and the manifest, data, prompt projection, model
inventory/config, adapter, fit logs, protocols, and preflight receipt hashes
listed below matched the scorer's constants. This is not execution
authorization.

The current scorer differs from Iteration 173's scorer by the single missing
`9` inserted into `PREP_HELPER_SHA`. Deleting that byte in memory reproduced
the exact Iteration 173 scorer hash. Deleting the repaired `b` from
`TRAINER_SHA` as well reproduced the original pre-Iteration 173 scorer hash.
These exact digest matches confirm the intended two one-character literal
repairs and no other source-byte changes across the chain.

## HEAD and SHA-256 before/after

HEAD before and after: `af01304824f079a64b6c3902397a2034b843511a`. Each item
below was hashed before writing this report and rehashed after; the values
were unchanged.

| Item | SHA-256 before = after |
|---|---|
| Current scorer | `9E60927AE12D196F5CBE2C9C1F37E64C3FF3F2CA885B09EB7029BA75C5094B9E` |
| Iteration 175 repair report | `F9EF938A7CFB6D82FEA43217C7ADF694D36342EB369B22B6E47C065B51658275` |
| Trainer | `1D7CCBB42AF72C41066D52A4CB6448D000C07D395657CAE475DAAA79363B49B5` |
| Prompt projection helper | `92E90F2F323BAC9F917C06DE318FA3B4E89EC0FD5FC7DC00989E2A7EF3ED88B8` |
| Evaluation protocol | `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6` |
| Training protocol | `4B123714BB3C669A98B4D892BD127D69A10ADCDB6763CC4059B66FAE128E9893` |
| Pinned-tree helper | `E7BFCA60ADBE5E4284392C878BF9EE6B401C5B92C396FF631AE4D4ABBBF3D499` |
| Fit manifest | `D39A9335FBDD107390F053F2460A34845CE3EFE2EA473F73060C6EAE85278F0E` |
| Fit resource log | `5812CD2BE242B407CBA8EFE8E04813D6973BCB2B9CD61A958849B491B7DFB781` |
| Fit epoch metrics | `889F5FCA08FAA5C5845BF2C8F2168A371F91108ADBFCAD55FE28B9D384AA765D` |
| Fit preflight manifest | `6EA37A8BA9A1B75CC1E4749085E7EB50E456BFAE039FAF6E74417EF3DCC353C4` |
| Fit preflight resource log | `0629B827E4704445BF3E456B331A8C917C0B135460C019FA99C88D514A769732` |
| Model inventory | `30B09CF32F06FAE5418A0B925820202BFDDF9E1C2A1F009D12E6396D10AED15A` |
| Model config | `DDC63E1C717AFA86C865BB5E01313D89D72BB53B97AD4A8A03BA8510C0621670` |
| Dataset manifest | `11683129106FF2448930818D6631B8E76201798893E7587ECB0872CBF6BCEBED` |
| Synthetic dev source (hash only) | `EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7` |
| Prompt-only projection | `6BE3C1E65342711AF8FCB7C6F44ED53B5986D31AD93FE0C9EE1542E537268BAF` |
| Prompt projection manifest | `DC4C3B605F7CC2AC62AA283BDD90B55FBCDA7CB4BF526441306EC25508167939` |
| Adapter weights | `051A942CC306D15FF22AD300D6256CC4B8E6335B9C6263B65696353B04938E5C` |
| Adapter config | `F77ECF3C2E87B2586563F3CA6017B74F62B180C31F67260A590CCFF85453531F` |
| Adapter README | `D402F188EBE4AA2ABEB5929611EE4C919D4DAEE9B69751E499696F871F82DC96` |

The Iteration 173 scorer baseline digest is
`5B92E5EC7A325B82C265FB082350EF3664361229B850F70B79F31C75A2D255AF`.
Deleting the repaired helper-pin character from the current scorer reproduces
it exactly. The Iteration 175 report's actual filename is
`iteration-175-qwen35-4b-dev-helper-pin-repair-20260929.md`; its digest
matches the assignment's expected digest.

## Pin and gate findings

- `FIT_MANIFEST_SHA`, `FIT_RESOURCES_SHA`, `FIT_EPOCHS_SHA`, trainer,
  training-protocol, and fit-preflight receipt constants match their exact
  local files. The fit manifest metadata reports `runner_sha256` equal to
  the trainer digest and matches the pinned training protocol, model
  inventory/config, dataset manifest, and synthetic dev source hashes.
- `PREP_HELPER_SHA` is the full 64-character SHA-256 of the actual helper.
  The prompt manifest and the scorer's expected projection metadata bind this
  helper identity. The prompt-only JSONL and manifest match their constants.
- The three adapter files match the exact hashes and byte sizes recorded by
  the fit manifest and checked by the scorer. The pinned-tree helper file also
  matches its source constant.
- Full-score admission still checks exact scorer/protocol/fit/input/runtime/
  device/reservation identities, sealed prediction hashes, resource samples,
  and both-arm preflight generation success before loading the prompt
  projection or inference runtime. The preflight path checks both arms and
  seals their outputs before its success/failure receipt is written.
- The source still loads only prompt messages for generation and seals both
  prediction files before scoring references. No provider call, credential
  access, adapter activation, or active-state mutation was introduced by the
  two literal repairs.

## Scope limits

The prompt-only artifact, its manifest, and the allowed synthetic dev source
were hashed; the source contents were not parsed or displayed. No oracle or
held-out path was opened, hashed, parsed, enumerated, or resolved. No Python,
AST/syntax check, tests, tokenizer/runtime/model import, inference, benchmark,
training, network/provider/SubRoute request, or credential access was run.

The model inventory file and config were verified, but the 14 model snapshot
weight shards were not traversed or rehashed. The scorer's pinned-tree check
is the runtime mechanism that verifies the snapshot tree. The chat-template
pin was compared through the frozen fit metadata; it was not recalculated
from a tokenizer because runtime imports were excluded. These are static
review limits, not test results.

At the latest resource sample, 24.59% system RAM was free (8,234,888 KiB of
33,486,624 KiB); the pinned RTX 5060 Ti had 15,214 of 16,311 MiB VRAM free.
No workload was started. The assigned review reservation is 50,000 bytes;
this report is under that bound. Fresh resource and storage admission are
required before any later job.

Read-only commands included `git rev-parse HEAD`, explicit `Get-FileHash`
calls for the listed files, bounded `Get-Content`/`rg` inspection, and
in-memory byte-deletion/hash comparisons for the two literal repairs. No
source file was changed. The only new file is this review report.

**A static pass is not execution permission.** No preflight or score-dev job
is authorized by this report.
