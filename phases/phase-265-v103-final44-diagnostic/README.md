# Phase 265: v103 sealed final-slice diagnostic

Status: `PASS_MECHANICAL_WORKER`, diagnostic only.

The current v103 portable package was replayed against all 44 rows in
`evals/wrench-expanded-v2/final.jsonl` using the existing matched teacher
traces. This is a separate sealed-slice diagnostic, not a release claim. The
evaluation suite remains marked `DRAFT_PENDING_HUMAN_APPROVAL`, and no result
from this run was used for training, routing selection, or prompt tuning.

## Result

- trace count: `44`
- eligible mechanical traces: `24`
- Wrench plus identical MiniMax fallback final success: `1.0`
- Wrench verifier success: `1.0`
- weighted mechanical frontier-token coverage: `1.0`
- net frontier-token savings: `1.0`
- frontier fallback tokens: `0`
- local tokens: `4805`
- median / p95 latency: `195.803 ms` / `301.136 ms`
- prohibited accepts: `0`
- unexpected mutations: `0`

The teacher-only arm's weighted final success was `0.7831305` on this slice,
while the Wrench arm was `1.0`. This is not a claim that Wrench is generally
better than MiniMax because the slice is not human-approved, the suite is not
production-authorized, and the 44 rows are not independent proof of the full
North Star.

Evidence:

- `evaluation.json`
- `trace-manifest.json`

