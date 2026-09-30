# Iteration 169: Qwen3.5-4B dev evaluation source repair

Status: source package repaired; development projections prepared offline;
inference remains blocked pending independent review and a separately admitted
preflight job. This report makes no task-quality, savings, or product-acceptance
claim.

## Repairs

- Split the frozen 64-row synthetic dev payload in a separate offline helper
  into prompt-only and oracle-only files. Only the prep helper reads the
  combined labeled source. The scorer loads prompts alone; full score opens
  oracle data only after both arms' prediction files are flushed and hashed.
  Preflight does not open oracle data. No held-out data was accessed.
- Added root-confinement and reparse-point checks over every planned output,
  log, and scratch path before the first directory creation, then repeats
  checks around writes. Ordinary path operations still have a TOCTOU race if a
  concurrent actor swaps components between checking and opening; the protocol
  states that limitation rather than claiming race-free confinement.
- Strengthened full-score admission to require exact preflight bindings for
  model ID/revision/config/inventory, dataset and dev source hashes, prompt
  projection and manifest hashes, adapter and fit identities, Python/runtime
  module identities, GPU UUID/name/total, reservation record bytes and digest,
  both sealed prediction-file hashes, and the resource-log hash and samples.
- Reworded the Transformers `max_time=300` behavior as cooperative. The
  protocol requires an external hard job timeout of 900 seconds for preflight
  and 14,400 seconds for full score. The scorer itself does not implement a
  hard per-generation cancellation mechanism.
- Guarded failure-report writes and capped projection inputs and outputs.
  Candidate remains inactive and is loaded read-only by the scorer.

## Prepared development projections

The only artifact-producing command run for this repair was:

```powershell
python tools/prepare_gateway_lora_screen_03_4b_dev.py --storage-reservation-job-id WRENCH-QWEN35-4B-DEV-EVAL-REPAIR-ITER169-20260929
```

It consumed the pinned synthetic dev source (SHA-256
`EE0F6DE198CB1D6C6B4EA19A138CCDA9F0D9F1562232430A0A9CE15307760AA7`) and
created four new files under
`C:\wrench-slm-data\artifacts\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-projections-iter169`:

| File | Bytes | SHA-256 |
|---|---:|---|
| `prompt-only.jsonl` | 60,203 | `6BE3C1E65342711AF8FCB7C6F44ED53B5986D31AD93FE0C9EE1542E537268BAF` |
| `prompt-manifest.json` | 861 | `DC4C3B605F7CC2AC62AA283BDD90B55FBCDA7CB4BF526441306EC25508167939` |
| `oracle-only.jsonl` | 14,612 | `B6AC5D5C81A1390CC8A9A12D065E8C58CD62242A3308C754641424B1CF783701` |
| `oracle-manifest.json` | 853 | `B23449AE7809432B1C5EAD7D915B7E8D635EF48FE882CBB7FBCDF8742E1C675E` |

Total new projection data: 76,529 bytes. Helper SHA-256:
`92E90F2F323BAC9F917C06DE318FA3B4E89EC0FD5FC7DC00989E2A7EF3ED88B8`.
The prep command verified the exact active 5,000,000-byte ITER169 reservation,
source hash, output caps, and destination free-space floor. The reservation is
left active for the owner to account and release.

## Source identities and scope

Repository HEAD remains `af01304824f079a64b6c3902397a2034b843511a`.
Final source hashes:

- Scorer `tools/score_gateway_lora_screen_03_4b_dev.py`: SHA-256
  `233426CFFF1E5DBF479BEC0256A0DDB79896D6E3A3FAB47DADD6EA890C2052C9`.
- Prep helper `tools/prepare_gateway_lora_screen_03_4b_dev.py`: SHA-256
  `92E90F2F323BAC9F917C06DE318FA3B4E89EC0FD5FC7DC00989E2A7EF3ED88B8`.
- Protocol `docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md`:
  SHA-256 `079B17BC7848E85AC9B1764864F78C2D7AF911150517EFEF12FAAE87E9A3F341`.
- This report's SHA-256 is returned out of band because embedding it here
  would change the report bytes.

Only those two tool files, the evaluation protocol, and this report were edited
or added in the repository. The repository had unrelated pre-existing changes;
this repair did not stage or modify them.

## Not run and remaining gates

No scorer invocation, preflight, full score, model/runtime/tokenizer import,
inference, benchmark, test, AST check, provider/SubRoute request, credential
read, adapter activation, or held-out access was performed. The fit candidate
remains inactive. Before inference, independently review the exact package,
verify fresh storage and at least 10% RAM/VRAM free, create a unique reservation
of at least 500 MB for preflight or 1 GB for full scoring, retain 5 GiB of
destination headroom, and enforce the protocol's external hard job timeout.
Even a successful 64-row synthetic diagnostic cannot establish all-day coding
reliability, Frontier savings, or the gateway acceptance targets.
