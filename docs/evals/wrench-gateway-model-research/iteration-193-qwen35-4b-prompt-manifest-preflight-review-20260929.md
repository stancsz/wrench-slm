# Iteration 193: Qwen3.5-4B prompt-manifest preflight review

Assignment: `WRENCH-QWEN35-4B-PROMPT-MANIFEST-PREFLIGHT-REVIEW-ITER193-20260929`  
Nonce: `f2ae7861-ab05-4042-997f-a5a24e97d487`  
Verdict: **PASS for a fresh one-prompt preflight only.** Static review only; no execution authority is granted.

## Exact identities

| Item | SHA-256 / identity |
|---|---|
| Repository HEAD before review | `af01304824f079a64b6c3902397a2034b843511a` |
| Repository HEAD after review | `af01304824f079a64b6c3902397a2034b843511a` |
| Scorer before and after | `4E2E69E1AE89B553470FE3ABE9EE5776C70D35942B99E8B4509C7FA71F159E85` |
| Evaluation protocol before and after | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Active gateway goal | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| Iteration 192 manifest-binding fix report | `D416C34C05CCE381F227F305EB7591C0C0599C78A1834D864F52260F04C99B9E` |
| Iteration 191 full-score HOLD report | `49A17FD073F0BAC721BE050C5A6DA0A0F6F54B5B764D5E4008ABAFBF97C5B6D2` |

## Findings

`load_prompt_projection()` verifies the pinned manifest bytes against `PROMPT_MANIFEST_SHA` and returns `sha_bytes(manifest_bytes)`. The preflight receipt writes this returned digest to `prompt_manifest_sha256`; it separately writes `PROMPT_PROJECTION_SHA` to `prompt_projection_sha256`. Thus the manifest and payload identities stay distinct and match the direct score-mode comparisons.

The fit loader hashes the raw fit manifest, compares it to the pinned fit-manifest SHA, and returns that actual digest. The receipt writes it as `training_manifest_sha256`, while `training_protocol_sha256` is the separate pinned training-protocol hash. Score mode compares both separately. The receipt also binds the current evaluator SHA, evaluation-protocol SHA, model/revision/config/inventory, dataset and dev hashes, adapter SHA, runtime identity, GPU identity, reservation identity, chat template, and `frontier_calls: 0`. A new preflight made with this scorer therefore binds the reviewed evaluator identity; preflight 09, which names an older scorer SHA, remains stale and must not be used.

Preflight reads the pinned prompt-only projection, limits the run to its first row, and runs base and LoRA against the same transformed messages. It does not read oracle data in preflight. Both prediction files are sealed and hashed; the receipt is marked completed only when both generations pass the successful-generation checks. The score gate checks the receipt’s status, prediction hashes and shared example ID, failure details, resource-log hash and summary, and rejects errors, timeouts, budget overruns, or resource-floor breaches before it proceeds to model loading. Model and tokenizer loading is local-only, with offline flags and `trust_remote_code=False`; no provider route is present. The one-prompt workflow retains unique job IDs, reservation and destination-headroom checks, bounded output and scratch limits, root/reparse path checks, resource monitoring, and the 10% RAM/VRAM floors. The 300-second generation limit is cooperative; the protocol specifies external supervision of the 900-second preflight wall-clock limit.

This review supports only attempting a **new** one-prompt preflight after fresh storage reservation and live resource admission. It does not approve or start inference. Preflight 09 is stale. A successful new preflight would still require a separate exact-hash full-score package review, a separate reservation of at least 1 GB, fresh resource admission, and accounting for storage and reservation state. No 64-row score, provider call, held-out access, or product-acceptance claim is authorized by this review.

## Review-time resources and scope

RAM free at review: `30.57%` (`10,236,648 / 33,486,624` KiB). RTX 5060 Ti: `15,223 / 16,311` MiB VRAM free. These samples are review-time observations, not preflight admission; check again before the job and monitor throughout.

Commands used: `git rev-parse HEAD`; `Get-FileHash` for the assigned scorer, protocol, active gateway goal, and Iteration 191/192 reports; bounded `Get-Content` for scorer functions, score gates, protocol and prior report; `rg` searches restricted to the scorer; `Get-CimInstance Win32_OperatingSystem`; and `nvidia-smi --query-gpu=uuid,name,memory.total,memory.free --format=csv,noheader,nounits`.

No prompt or oracle payload was opened. No tests, Python/runtime command, model load, inference, benchmark, network/provider/SubRoute call, credential access, spending, or source edit occurred. Only this review report was created.
