# Iteration 171: preflight failure handling repair

Status: source-only repair complete. No inference was started.

The scorer now marks preflight `PREFLIGHT_COMPLETED` only if both the base and
LoRA generation have no runtime error or cooperative 300-second `max_time`
overrun, elapsed time below 300 seconds, nonempty prompt encoding and
completion, completion below the 96-token cap, nonempty output, and valid
schema. Otherwise it seals both prediction files and writes a
`PREFLIGHT_FAILED` receipt with per-arm failure codes and pinned identities,
then exits nonzero. The normal outer failure record is also retained.

Full-score admission verifies both preflight prediction hashes, parses and
checks each sealed arm for the recorded shared example ID and generation
success predicate, and verifies the exact resource-log hash, samples, and
summary before it loads prompts or enters model inference. A failed status,
prediction error, timeout, time/token budget overrun, empty output, or invalid
schema blocks scoring.

Transformers `max_time` remains cooperative. The protocol requires an external
hard wall-clock supervisor (900 seconds for preflight, 14,400 seconds for full
score). The supervisor must leave a `failure.json` receipt if it stops a job;
if both arms were not sealed, that receipt must state that explicitly.

## Files and identities

Repository HEAD remains `af01304824f079a64b6c3902397a2034b843511a`.

- `tools/score_gateway_lora_screen_03_4b_dev.py`: SHA-256
  `14EC4C0939E8135A14D31A9A93E51DE6DF01DA658E6F42A3369967E94C4C2D05`.
- `docs/evals/wrench-gateway-model-research/lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md`:
  SHA-256 `328CDD2A156288D25F1665C10DC46DB2FD84D0D009F294D2D10185839A9D2CA6`.
- This report is the only additional path added for Iteration 171.
- The Iteration 169 prompt/oracle projections and their hashes were not
  modified. The prep helper and Iteration 170 report were not modified.

Only these commands were used for final identity accounting:

```powershell
Get-FileHash -LiteralPath tools\score_gateway_lora_screen_03_4b_dev.py,docs\evals\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md -Algorithm SHA256
git rev-parse HEAD
git status --short -- tools\score_gateway_lora_screen_03_4b_dev.py docs\evals\wrench-gateway-model-research\lora-screen-03-qwen35-4b-dev-eval-protocol-20260929.md docs\evals\wrench-gateway-model-research\iteration-171-qwen35-4b-dev-eval-failure-repair-20260929.md
```

No test, AST check, projection helper, model/runtime/tokenizer import,
preflight, full scoring, provider/network/SubRoute request, credential read,
held-out access, or adapter activation was performed. Independent review and
fresh resource/storage admission remain required before any preflight run.
