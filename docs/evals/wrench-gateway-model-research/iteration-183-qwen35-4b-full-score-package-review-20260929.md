# Iteration 183: Qwen3.5-4B full dev-score package review

Assignment: `WRENCH-QWEN35-4B-FULL-DEV-SCORE-PACKAGE-REVIEW-ITER183-20260929`  
Nonce: `6feaa056-6062-46f2-a390-205bf7d2149f`  
Verdict: **PASS for the bounded 64-row synthetic dev score package**. This is
static review only; it does not launch or reserve the score job.

## Exact identities

| Item | Verified SHA-256 or identity |
|---|---|
| Repository HEAD, before and after | `af01304824f079a64b6c3902397a2034b843511a` |
| Scorer | `86040E775FE5EC60B9C018BA3BD0DA82F07A14C24C972A754720C0B0CCB8AABF` |
| Schema-contract protocol | `2855EBC773272CBF1C296F99BC2774F156876A574DA500601675BA8ACEE2E85F` |
| Gateway goal | `2FB13F31D4B6D528A5EDD92891980A8B81965BE1AE1694ABA76350193400BE59` |
| Iteration 181 report | `D3AFD4AE7AB8081EE389B27C77A91C999066723DD686DB7EEF77ACD44B6A6F2B` |
| Iteration 182 report | `124B958E9193E5A00A9E62DDF0831D7C45B2B5F63558A18CFA5EE92C879133F9` |
| Successful preflight 08 receipt | `71F4F188D6D45D48F338ED0F301A6B8A6C8103BE564B9F0BC7EBDB59B31242E2` |
| Preflight base predictions | `7854C5937276B3F212C4DD135F9972F30907120C7F4A3062C9A185CB877CBE9C` |
| Preflight LoRA predictions | `7CDAF6ED1E507836B02F64A4ED27F23B0D6D0DC4E6FF71CA280D538709EF81E0` |
| Preflight resource log | `BDB3D81FCDC5C85EC1B1B37774ACB4B5E85B59D8E41E3432951F62D5C0A05707` |

The receipt reports `PREFLIGHT_COMPLETED`, the expected repository HEAD,
Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, model config
and inventory pins, dataset and dev-source pins, adapter/fit pins, Python
3.13.15 and Torch/Transformers/PEFT/Accelerate identities, RTX 5060 Ti UUID,
prompt projection/manifest pins, matching one-row example IDs, both prediction
hashes, and the resource-log hash. These receipt and file hashes match the
assignment. The prompt and oracle payload files were not opened.

## Review findings

- `score-dev` requires a unique mode-specific reservation of at least
  1,000,000,000 bytes and at least 5 GiB destination headroom. It also checks
  the reservation while running. The Iteration 183 review reservation is only
  50,000,000 bytes and does not admit scoring. Obtain a fresh full-score
  reservation and storage-budget status before any score launch.
- The code accepts the preflight reservation as released when its record is
  absent; if the same reservation record remains active, it accepts it only
  when the bytes match the identity embedded in the receipt. It does not
  require release. At score admission, account for any still-active
  preflight reservation in the aggregate budget or release it after its
  outputs are accounted.
- Full scoring requires exactly 64 unique prompt rows from the pinned
  prompt-only projection. It persists and hashes both arm prediction files
  before `load_oracle_projection()` opens the separately pinned oracle file.
  Preflight does not open the oracle. No held-out path is referenced by the
  scorer.
- The strict validator checks the exact key set, route/operation/reason enums,
  boolean type, list-of-string evidence IDs, duplicate IDs, and membership in
  visible request IDs. Authority-like extra keys fail the exact key-set
  check; authority violations are also recorded. The closed route values are
  output labels only. Scoring has no provider client or provider route.
- Local model/tokenizer loading is pinned to files with `local_files_only`,
  offline environment flags, and `trust_remote_code=False`. The adapter is
  loaded read-only. Subprocess use is limited in source to Git identity and
  `nvidia-smi` resource sampling.
- Output/scratch roots are checked beneath the approved data root; reparse
  ancestors are rejected, one-shot paths are refused, per-file outputs cap at
  20 MiB, aggregate evaluation output caps at 128 MiB, and scratch caps are
  512 MiB for full score. Path checks are cooperative and retain the documented
  time-of-check/time-of-use limitation.
- Resource monitoring samples RAM/VRAM once per second and interrupts on a
  drop below 10%, wrong GPU identity, scratch cap, reservation/headroom, or log
  cap breach. Preflight 08 recorded 89 samples, no breach, minimum free RAM
  24.11%, minimum free VRAM 6,148/16,311 MiB (37.69%), and zero scratch bytes.
- The fixed enum/schema contract is appended identically for both arms after
  projection hashes are verified. The one-row preflight is only a schema and
  local-runtime gate. Neither it nor the 64-row synthetic score supports a
  product effectiveness, savings, or all-day engineering claim.
- `max_time=300` is explicitly cooperative. The protocol requires an external
  hard job timeout and a failure receipt if the supervisor stops a job.

The source checks current HEAD and exact scorer/protocol hashes. It does not
compare the preflight receipt's `repo_head` field directly, although the
verified successful receipt records the expected HEAD and its evaluator and
protocol hashes match. This is a minor receipt-validation omission, not a
blocker for this one pinned local score; preserve the receipt hash with the
result.

## Resource sample and review scope

Review-time sample: system RAM free `30.85%` (`10,329,528 / 33,486,624` KiB);
GPU `GPU-f36264bc-c100-4a58-d6a5-a4d3420a3021`, RTX 5060 Ti, `15,208 / 16,311`
MiB free. This is a review-time observation, not a full-score admission. Recheck
both floors immediately before and throughout any score job.

Commands used were limited to `git rev-parse HEAD`, `Get-FileHash` on the
assigned source/docs/reports/receipt/prediction/resource files,
bounded `Get-Content` on the scorer, protocol, reports, and preflight receipt,
`rg` searches restricted to the scorer, `Get-CimInstance Win32_OperatingSystem`,
and `nvidia-smi` resource queries. No tests, Python command, model/runtime
load, inference, benchmark, network/provider/SubRoute call, credential access,
source mutation, prompt/oracle payload read, or held-out access occurred.

Only this review report was created. No score job was launched.
